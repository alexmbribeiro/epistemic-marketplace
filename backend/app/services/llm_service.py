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
            return await client.aio.interactions.create(**kwargs)
        except Exception as exc:
            retryable = getattr(exc, "status_code", None) in _RETRYABLE_CODES
            if not retryable or attempt == settings.agent_max_retries:
                raise
            delay = min(2**attempt, 30) + random.uniform(0, 1)
            logger.warning(
                "Gemini %s, retrying in %.1fs (attempt %d/%d)",
                getattr(exc, "status_code", "?"), delay, attempt + 1, settings.agent_max_retries,
            )
            await asyncio.sleep(delay)


async def run_agent_turn(system_prompt: str, user_message: str, schema: dict) -> dict:
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
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned malformed JSON: {raw[:200]}") from exc
