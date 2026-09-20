import anthropic

from app.config import settings

_client = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
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


async def run_agent_turn(system_prompt: str, user_message: str, schema: dict) -> dict:
    client = get_client()
    response = await client.messages.create(
        model=settings.agent_model,
        max_tokens=settings.agent_max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        thinking={"type": "adaptive"},
        output_config={"effort": settings.agent_effort},
        tools=[{"name": "output", "description": "Output your structured epistemic position", "input_schema": schema}],
        tool_choice={"type": "tool", "name": "output"},
    )
    if response.stop_reason == "max_tokens":
        raise ValueError(
            f"Agent turn truncated at max_tokens={settings.agent_max_tokens}; "
            "raise AGENT_MAX_TOKENS or lower AGENT_EFFORT"
        )
    for block in response.content:
        if block.type == "tool_use" and block.name == "output":
            return block.input
    raise ValueError("No structured output returned from Claude")
