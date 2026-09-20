import uuid
from dataclasses import dataclass, field

from app.services import claude_service


@dataclass
class AgentResult:
    agent_id: str
    agent_name: str
    archetype: str
    round_number: int
    belief_score: float
    confidence_low: float
    confidence_high: float
    reasoning: str
    key_evidence: list[str]
    cruxes: list[str]
    argument_type: str
    argument_content: str
    argument_strength: float
    unanswered_questions: list[str]
    challenges: list[dict] = field(default_factory=list)
    synthesis_notes: str = ""


class BaseAgent:
    archetype: str = "base"
    name: str = "Base Agent"
    description: str = ""
    system_prompt: str = ""

    def __init__(self, agent_id: str | None = None, config: dict | None = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.config = config or {}

    def _build_system_prompt(self) -> str:
        return self.system_prompt

    async def form_position(self, claim: str) -> AgentResult:
        prompt = f"""A claim has been submitted for epistemic evaluation:

CLAIM: "{claim}"

Evaluate this claim independently. Do not assume consensus. Apply your cognitive architecture strictly."""

        result = await claude_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            claude_service.POSITION_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=1,
            **{k: result[k] for k in result},
        )

    async def challenge(self, claim: str, others: list[AgentResult]) -> AgentResult:
        others_summary = "\n".join(
            f"- {r.agent_name} ({r.archetype}): belief={r.belief_score:.2f}, argument={r.argument_content}"
            for r in others if r.agent_id != self.agent_id
        )
        prompt = f"""CLAIM: "{claim}"

Other agents have formed their initial positions:
{others_summary}

Now review these positions and form your updated position. Challenge positions you disagree with. Specify which agent you are challenging and why."""

        result = await claude_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            claude_service.CHALLENGE_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=2,
            challenges=result.get("challenges", []),
            **{k: result[k] for k in result if k != "challenges"},
        )

    async def synthesize(self, claim: str, round1: list[AgentResult], round2: list[AgentResult]) -> AgentResult:
        r1_summary = "\n".join(
            f"- {r.agent_name}: belief={r.belief_score:.2f} | {r.argument_content}"
            for r in round1
        )
        r2_summary = "\n".join(
            f"- {r.agent_name}: belief={r.belief_score:.2f} | {r.argument_content}"
            for r in round2 if r.agent_id != self.agent_id
        )
        prompt = f"""CLAIM: "{claim}"

ROUND 1 — Initial positions:
{r1_summary}

ROUND 2 — Cross-challenges:
{r2_summary}

Now synthesize. Has your view changed? Why or why not? Provide your final position."""

        result = await claude_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            claude_service.SYNTHESIS_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=3,
            synthesis_notes=result.get("synthesis_notes", ""),
            **{k: result[k] for k in result if k != "synthesis_notes"},
        )
