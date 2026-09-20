from app.agents.adlerian import AdlerianAgent
from app.agents.analogist import AnalogistAgent
from app.agents.aristotle import AristotelianAgent
from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.bayesian import BayesianAgent
from app.agents.contrarian import ContrarianAgent
from app.agents.dialectician import DialecticianAgent
from app.agents.domain_expert import DomainExpertAgent
from app.agents.falsificationist import FalsificationistAgent
from app.agents.frequentist import FrequentistAgent
from app.agents.hume import HumeanAgent
from app.agents.jung import JungianAgent
from app.agents.kant import KantianAgent
from app.agents.nietzsche import NietzscheanAgent
from app.agents.pragmatist import PragmatistAgent
from app.agents.wittgenstein import WittgensteinianAgent

ARCHETYPE_MAP = {
    # Method archetypes
    "bayesian": BayesianAgent,
    "falsificationist": FalsificationistAgent,
    "analogist": AnalogistAgent,
    "contrarian": ContrarianAgent,
    "dialectician": DialecticianAgent,
    "frequentist": FrequentistAgent,
    "domain_expert": DomainExpertAgent,
    # Thinkers. Each is here for a test none of the others makes, not for the
    # name: genealogy, symbolic compensation, the four causes, impressions and
    # the is/ought gap, conditions of possibility, grammatical dissolution,
    # practical consequences, purpose over cause.
    "nietzschean": NietzscheanAgent,
    "jungian": JungianAgent,
    "aristotelian": AristotelianAgent,
    "humean": HumeanAgent,
    "kantian": KantianAgent,
    "wittgensteinian": WittgensteinianAgent,
    "pragmatist": PragmatistAgent,
    "adlerian": AdlerianAgent,
}

# Used when a debate does not name its agents.
DEFAULT_ARCHETYPES = [
    "bayesian",
    "falsificationist",
    "analogist",
    "contrarian",
    "dialectician",
    "frequentist",
]

THINKER_ARCHETYPES = [
    "nietzschean",
    "jungian",
    "aristotelian",
    "humean",
    "kantian",
    "wittgensteinian",
    "pragmatist",
    "adlerian",
]

# Seeded at startup and selectable. domain_expert is excluded: it is a shell
# that needs a domain in its config, so it is authored per use rather than
# seeded. A thinker is selectable but never default — it joins because
# someone chose it.
SEEDED_ARCHETYPES = DEFAULT_ARCHETYPES + THINKER_ARCHETYPES


def build_agent(
    archetype: str,
    agent_id: str,
    config: dict | None = None,
    system_prompt: str | None = None,
    name: str | None = None,
) -> BaseAgent:
    """An unknown archetype is a user-authored agent: BaseAgent carrying its
    stored prompt, name and archetype label."""
    cls = ARCHETYPE_MAP.get(archetype, BaseAgent)
    return cls(
        agent_id=agent_id,
        config=config or {},
        system_prompt=system_prompt,
        name=name,
        archetype=archetype,
    )
