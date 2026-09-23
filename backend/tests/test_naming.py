"""Matching a name the model wrote against an actual agent.

The model names agents in whichever form it reaches for. An early version
asked whether the written name appeared inside the label, which fails for
every adjectival form — "wittgensteinian" is not a substring of
"wittgenstein", it is longer — and silently dropped 60% of challenge edges.
"""

import pytest

from app.core.naming import resolve_agent

ROSTER = [
    {"label": "Wittgenstein (R1)", "archetype": "wittgensteinian"},
    {"label": "Kant (R1)", "archetype": "kantian"},
    {"label": "Marx (R1)", "archetype": "marxist"},
    {"label": "Weil (R1)", "archetype": "weilian"},
]


@pytest.mark.parametrize(
    "written,expected",
    [
        ("Wittgenstein", "Wittgenstein (R1)"),
        ("wittgensteinian", "Wittgenstein (R1)"),
        ("Kantian", "Kant (R1)"),
        ("the Kantian agent", "Kant (R1)"),
        ("the Marxist", "Marx (R1)"),
        ("WEIL", "Weil (R1)"),
    ],
)
def test_resolves_the_forms_the_model_actually_writes(written, expected):
    assert resolve_agent(written, ROSTER)["label"] == expected


@pytest.mark.parametrize("written", ["", "   ", "Nietzsche", "nobody", "the agent"])
def test_returns_none_for_someone_who_is_not_here(written):
    """Matching too eagerly would attribute a challenge to the wrong agent."""
    assert resolve_agent(written, ROSTER) is None


def test_objects_work_as_well_as_dicts():
    class A:
        name = "Kant"
        archetype = "kantian"

    assert resolve_agent("the Kantian", [A()]) is not None
