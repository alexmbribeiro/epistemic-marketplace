import uuid
from dataclasses import dataclass, field

from app.core.naming import resolve_agent
from app.services import llm_service


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

    def __init__(
        self,
        agent_id: str | None = None,
        config: dict | None = None,
        system_prompt: str | None = None,
        name: str | None = None,
        archetype: str | None = None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.config = config or {}
        # The stored record wins over the class defaults. For the six seeded
        # archetypes these are identical; for a user-authored agent the record
        # is the only source of a persona, and without this it would debate
        # with an empty system prompt.
        if system_prompt:
            self.system_prompt = system_prompt
        if name:
            self.name = name
        if archetype:
            self.archetype = archetype

    def _build_system_prompt(self) -> str:
        return self.system_prompt

    async def form_position(self, claim: str) -> AgentResult:
        prompt = f"""A claim has been submitted for epistemic evaluation:

CLAIM: "{claim}"

Evaluate this claim independently. Do not assume consensus. Apply your cognitive architecture strictly."""

        result = await llm_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            llm_service.POSITION_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=1,
            **{k: result[k] for k in result},
        )

    async def challenge(self, claim: str, others: list[AgentResult]) -> AgentResult:
        def describe(r: AgentResult) -> str:
            # Cruxes included on purpose: without them an agent can only argue
            # against a headline, never against what would actually move the
            # other's mind.
            cruxes = "; ".join(r.cruxes[:2]) if r.cruxes else "none stated"
            return (
                f"- {r.agent_name} ({r.archetype}): belief={r.belief_score:.2f}\n"
                f"    argument: {r.argument_content}\n"
                f"    would change their mind: {cruxes}"
            )

        others_summary = "\n".join(describe(r) for r in others if r.agent_id != self.agent_id)
        prompt = f"""CLAIM: "{claim}"

Other agents have formed their initial positions:
{others_summary}

Now review these positions and form your updated position. Challenge positions you disagree with. Specify which agent you are challenging and why."""

        result = await llm_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            llm_service.CHALLENGE_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=2,
            challenges=result.get("challenges", []),
            **{k: result[k] for k in result if k != "challenges"},
        )

    def _challenges_against(self, round2: list[AgentResult]) -> list[tuple[str, dict]]:
        """The challenges other agents aimed at this one.

        Targets are written by the model in whatever form it likes, so they
        have to be resolved rather than compared.
        """
        me = [{"label": self.name, "archetype": self.archetype}]
        aimed = []
        for r in round2:
            if r.agent_id == self.agent_id:
                continue
            for ch in r.challenges or []:
                if resolve_agent(ch.get("target_agent", ""), me) is not None:
                    aimed.append((r.agent_name, ch))
        return aimed

    async def synthesize(self, claim: str, round1: list[AgentResult], round2: list[AgentResult]) -> AgentResult:
        r1_summary = "\n".join(
            f"- {r.agent_name}: belief={r.belief_score:.2f} | {r.argument_content}"
            for r in round1
        )
        r2_summary = "\n".join(
            f"- {r.agent_name}: belief={r.belief_score:.2f} | {r.argument_content}"
            for r in round2 if r.agent_id != self.agent_id
        )
        # Challenges used to be produced, stored, drawn as arrows — and never
        # delivered to the agent they were aimed at, which left every agent
        # synthesising against headlines it had already seen.
        aimed = self._challenges_against(round2)
        if aimed:
            addressed = "\n".join(
                f"- {who} ({ch.get('type', 'contradicts')}): {ch.get('challenge', '')}"
                for who, ch in aimed
            )
            challenge_block = (
                f"\n\nCHALLENGES ADDRESSED TO YOU:\n{addressed}\n\n"
                "Answer these directly. Say which land and which do not, and why. "
                "Conceding a good challenge is not a loss; ignoring one is."
            )
        else:
            challenge_block = "\n\nNobody challenged you directly this round."

        prompt = f"""CLAIM: "{claim}"

ROUND 1 — Initial positions:
{r1_summary}

ROUND 2 — Updated positions:
{r2_summary}{challenge_block}

Now synthesize. Has your view changed? Why or why not? Provide your final position."""

        result = await llm_service.run_agent_turn(
            self._build_system_prompt(),
            prompt,
            llm_service.SYNTHESIS_SCHEMA,
        )
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            archetype=self.archetype,
            round_number=3,
            synthesis_notes=result.get("synthesis_notes", ""),
            **{k: result[k] for k in result if k != "synthesis_notes"},
        )
