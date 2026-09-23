"""Forcing a model response to match its declared schema.

Gemini treats a schema as a strong hint rather than a contract: it drops
required fields, invents enum values, and wraps string array items in
objects. Anything reaching the database or the websocket has to match the
shape the frontend is typed against.
"""

import pytest

from app.services.llm_service import (
    POSITION_SCHEMA,
    Inconsistent,
    IncompleteOutput,
    _validate,
    is_retryable,
)


def _payload(**overrides):
    base = {
        "belief_score": 0.5,
        "probability_true": 0.5,
        "confidence_low": 0.4,
        "confidence_high": 0.6,
        "reasoning": "because",
        "key_evidence": ["a"],
        "cruxes": ["b"],
        "argument_type": "qualifies",
        "argument_content": "c",
        "argument_strength": 0.5,
        "unanswered_questions": [],
    }
    base.update(overrides)
    return base


def test_single_key_objects_are_unwrapped_to_strings():
    """React refuses to render {crux: "..."} where a string was declared."""
    out = _validate(_payload(cruxes=[{"crux": "unwrap me"}, "already a string"]), POSITION_SCHEMA)
    assert out["cruxes"] == ["unwrap me", "already a string"]
    assert all(isinstance(c, str) for c in out["cruxes"])


def test_enum_violations_are_clamped_to_a_declared_value():
    out = _validate(_payload(argument_type="refutes", probability_true=0.5), POSITION_SCHEMA)
    assert out["argument_type"] in POSITION_SCHEMA["properties"]["argument_type"]["enum"]


def test_numbers_arriving_as_strings_are_coerced():
    assert _validate(_payload(belief_score="0.42"), POSITION_SCHEMA)["belief_score"] == 0.42


def test_a_missing_required_field_is_raised_not_defaulted():
    """Filling it in would invent a confidence interval, which is worse than
    failing in an app whose entire output is calibrated uncertainty."""
    payload = _payload()
    del payload["confidence_low"]
    with pytest.raises(IncompleteOutput, match="confidence_low"):
        _validate(payload, POSITION_SCHEMA)


@pytest.mark.parametrize(
    "kind,probability,ok",
    [
        ("supports", 0.9, True),
        ("supports", 0.1, False),
        ("contradicts", 0.1, True),
        ("contradicts", 0.95, False),
        ("qualifies", 0.1, True),      # no constraint on the middle values
        ("uncertain", 0.9, True),
        ("supports", 0.48, True),      # inside the margin, not chased
    ],
)
def test_the_label_must_agree_with_the_number(kind, probability, ok):
    call = lambda: _validate(
        _payload(argument_type=kind, probability_true=probability), POSITION_SCHEMA
    )
    if ok:
        call()
    else:
        with pytest.raises(Inconsistent):
            call()


class _Boom(Exception):
    def __init__(self, message="", status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


@pytest.mark.parametrize(
    "exc,retryable",
    [
        (_Boom("rate limited", 429), True),
        (_Boom("server error", 503), True),
        (_Boom("bad request", 400), False),
        (_Boom("received 1011 (internal error) You exceeded your current quota"), True),
        (_Boom("something unexpected"), False),
        (IncompleteOutput("missing"), True),
        (Inconsistent("label vs number"), True),
    ],
)
def test_retry_classification(exc, retryable):
    """The Live API reports a rate limit two ways: an HTTP 429 with a
    status_code, and a websocket close with none at all. Matching only on the
    attribute let every quota error through unretried and killed whole juries."""
    assert is_retryable(exc) is retryable
