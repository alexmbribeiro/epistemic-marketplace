import asyncio
import json
import logging
import random

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

# 429 is the one that matters: a debate fires six calls at once, three rounds
# running, which trips free-tier per-minute limits easily.
_RETRYABLE_CODES = {429, 500, 502, 503, 504}


class IncompleteOutput(Exception):
    """The model answered but left required fields out.

    Gemini's function calling does not enforce `required` the way a forced
    Anthropic tool call did, and it drops fields on the larger schemas often
    enough to kill a debate. Re-asking fixes it; inventing the missing values
    would not — a fabricated confidence interval is worse than no answer in an
    app whose whole output is calibrated uncertainty.
    """


def _unwrap(value):
    """Gemini wraps scalars in single-key objects often enough to matter:
    cruxes comes back as [{"crux": "..."}] instead of ["..."]. The content is
    right, only the shape is wrong, so unwrap rather than reject."""
    if isinstance(value, dict) and len(value) == 1:
        inner = next(iter(value.values()))
        if isinstance(inner, (str, int, float, bool)):
            return inner
    return value


def _coerce(payload: dict, schema: dict) -> dict:
    """Force a response to match its declared schema.

    Gemini's function calling treats the schema as a strong hint, not a
    contract: it drops required fields, invents enum values, and wraps string
    array items in objects. Anything that reaches the database or the
    websocket has to match the shape the frontend is typed against.
    """
    props = schema.get("properties", {})
    out: dict = {}

    for key, value in payload.items():
        spec = props.get(key)
        if not spec:
            out[key] = value
            continue

        kind = spec.get("type")
        items = spec.get("items", {})

        if kind == "array":
            seq = value if isinstance(value, list) else [value]
            if items.get("type") == "object":
                out[key] = [_coerce(v, items) for v in seq if isinstance(v, dict)]
            else:
                out[key] = [str(_unwrap(v)) for v in seq]
        elif "enum" in spec and value not in spec["enum"]:
            fallback = "uncertain" if "uncertain" in spec["enum"] else spec["enum"][0]
            logger.warning("Coercing %s=%r to %r (outside enum)", key, value, fallback)
            out[key] = fallback
        elif kind == "string" and not isinstance(value, str):
            out[key] = str(_unwrap(value))
        elif kind == "number" and not isinstance(value, (int, float)):
            try:
                out[key] = float(_unwrap(value))
            except (TypeError, ValueError):
                out[key] = value
        else:
            out[key] = value

    return out


def _validate(payload: dict, schema: dict) -> dict:
    missing = sorted(set(schema.get("required", [])) - set(payload))
    if missing:
        raise IncompleteOutput(f"missing required fields: {', '.join(missing)}")
    return _coerce(payload, schema)

# A debate fans out to six agents per round. Firing all six at a free-tier
# per-minute limit gets most of them 429'd, and then they all back off in
# lockstep and collide again — a thundering herd. Gate concurrency instead;
# retries alone do not fix this.
_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.agent_max_concurrency)
    return _semaphore

_client = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


POSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "belief_score": {"type": "number", "description": "Probability claim is true, 0.0 to 1.0"},
        "confidence_low": {"type": "number", "description": "Lower bound of confidence interval"},
        "confidence_high": {"type": "number", "description": "Upper bound of confidence interval"},
        "reasoning": {"type": "string", "description": "Full reasoning chain"},
        "key_evidence": {"type": "array", "items": {"type": "string"}, "description": "Key evidence points"},
        "cruxes": {"type": "array", "items": {"type": "string"}, "description": "What would change your mind"},
        "argument_type": {"type": "string", "enum": ["supports", "contradicts", "qualifies", "redefines", "uncertain"]},
        "argument_content": {"type": "string", "description": "Core argument in one sentence"},
        "argument_strength": {"type": "number", "description": "Strength of this argument, 0.0 to 1.0"},
        "unanswered_questions": {"type": "array", "items": {"type": "string"}, "description": "Questions you cannot answer"},
    },
    "required": ["belief_score", "confidence_low", "confidence_high", "reasoning", "key_evidence", "cruxes", "argument_type", "argument_content", "argument_strength", "unanswered_questions"],
}

CHALLENGE_SCHEMA = {
    "type": "object",
    "properties": {
        "belief_score": {"type": "number"},
        "confidence_low": {"type": "number"},
        "confidence_high": {"type": "number"},
        "reasoning": {"type": "string"},
        "key_evidence": {"type": "array", "items": {"type": "string"}},
        "cruxes": {"type": "array", "items": {"type": "string"}},
        "argument_type": {"type": "string", "enum": ["supports", "contradicts", "qualifies", "redefines", "uncertain"]},
        "argument_content": {"type": "string"},
        "argument_strength": {"type": "number"},
        "challenges": {"type": "array", "items": {"type": "object", "properties": {"target_agent": {"type": "string"}, "challenge": {"type": "string"}, "type": {"type": "string", "enum": ["contradicts", "qualifies", "redefines"]}}, "required": ["target_agent", "challenge", "type"]}},
        "unanswered_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["belief_score", "confidence_low", "confidence_high", "reasoning", "key_evidence", "cruxes", "argument_type", "argument_content", "argument_strength", "challenges", "unanswered_questions"],
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "belief_score": {"type": "number"},
        "confidence_low": {"type": "number"},
        "confidence_high": {"type": "number"},
        "reasoning": {"type": "string"},
        "key_evidence": {"type": "array", "items": {"type": "string"}},
        "cruxes": {"type": "array", "items": {"type": "string"}},
        "argument_type": {"type": "string", "enum": ["supports", "contradicts", "qualifies", "redefines", "uncertain"]},
        "argument_content": {"type": "string"},
        "argument_strength": {"type": "number"},
        "synthesis_notes": {"type": "string", "description": "What changed from your initial position and why"},
        "unanswered_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["belief_score", "confidence_low", "confidence_high", "reasoning", "key_evidence", "cruxes", "argument_type", "argument_content", "argument_strength", "synthesis_notes", "unanswered_questions"],
}


async def _create_with_retry(client: genai.Client, **kwargs):
    # Matched on the status_code attribute rather than an exception class on
    # purpose: the SDK raises from google.genai._gaos.lib.compat_errors, which
    # is not a subclass of the public google.genai.errors.APIError and is not
    # re-exported anywhere public. Duck-typing survives that being reshuffled.
    for attempt in range(settings.agent_max_retries + 1):
        try:
            async with _get_semaphore():
                return await client.aio.interactions.create(
                    timeout=settings.agent_timeout_seconds, **kwargs
                )
        except Exception as exc:
            retryable = getattr(exc, "status_code", None) in _RETRYABLE_CODES
            if not retryable or attempt == settings.agent_max_retries:
                raise
            delay = min(2**attempt, 30) + random.uniform(0, 3)
            logger.warning(
                "Gemini %s, retrying in %.1fs (attempt %d/%d)",
                getattr(exc, "status_code", "?"), delay, attempt + 1, settings.agent_max_retries,
            )
            await asyncio.sleep(delay)


async def _live_turn(system_prompt: str, user_message: str, schema: dict) -> dict:
    """Run one agent turn over the Live (websocket) API.

    Why this exists: the free tier allows only ~20 requests/day against the
    regular model endpoint, which is one debate. The live model is not metered
    the same way. Two quirks make it work:

      - It rejects response_schema outright ("not supported in generation
        config"), so structured output goes through a function declaration
        instead — the same trick the Anthropic version used.
      - With tools declared it also rejects TEXT output, so we ask for AUDIO
        and never read it. The answer arrives on the tool-call channel, which
        is independent of the audio stream.
    """
    client = get_client()
    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": system_prompt,
        "tools": [
            {
                "function_declarations": [
                    {
                        "name": "output",
                        "description": "Report your structured epistemic position",
                        "parameters": schema,
                    }
                ]
            }
        ],
    }

    async with client.aio.live.connect(model=settings.agent_live_model, config=config) as session:
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": user_message}]},
            turn_complete=True,
        )
        async for msg in session.receive():
            tool_call = getattr(msg, "tool_call", None)
            if tool_call:
                for fc in tool_call.function_calls:
                    if fc.name == "output":
                        return _validate(dict(fc.args), schema)
            server_content = getattr(msg, "server_content", None)
            if server_content and getattr(server_content, "turn_complete", False):
                break

    raise ValueError("Live session ended without calling output")


async def _live_turn_with_retry(system_prompt: str, user_message: str, schema: dict) -> dict:
    for attempt in range(settings.agent_max_retries + 1):
        try:
            async with _get_semaphore():
                return await asyncio.wait_for(
                    _live_turn(system_prompt, user_message, schema),
                    timeout=settings.agent_timeout_seconds,
                )
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            retryable = (
                status in _RETRYABLE_CODES
                or isinstance(exc, (asyncio.TimeoutError, IncompleteOutput))
            )
            if not retryable or attempt == settings.agent_max_retries:
                raise
            delay = min(2**attempt, 30) + random.uniform(0, 3)
            logger.warning(
                "Live turn failed (%s: %s), retrying in %.1fs (attempt %d/%d)",
                type(exc).__name__, exc, delay, attempt + 1, settings.agent_max_retries,
            )
            await asyncio.sleep(delay)


async def run_agent_turn(system_prompt: str, user_message: str, schema: dict) -> dict:
    if settings.agent_backend == "live":
        return await _live_turn_with_retry(system_prompt, user_message, schema)

    client = get_client()
    interaction = await _create_with_retry(
        client,
        model=settings.agent_model,
        input=user_message,
        system_instruction=system_prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": schema,
        },
        generation_config={
            "max_output_tokens": settings.agent_max_tokens,
            "thinking_level": settings.agent_thinking_level,
        },
    )

    raw = interaction.output_text
    if not raw:
        # Usually means the response hit max_output_tokens before closing the
        # JSON, or a safety filter dropped it. Either way there is nothing to parse.
        raise ValueError(
            f"Gemini returned no text (status={interaction.status}); "
            f"raise AGENT_MAX_TOKENS or lower AGENT_THINKING_LEVEL"
        )
    try:
        return _validate(json.loads(raw), schema)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned malformed JSON: {raw[:200]}") from exc
