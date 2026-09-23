from app.agents.adlerian import AdlerianAgent
from app.agents.aristotle import AristotelianAgent
from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.dostoevsky import DostoevskianAgent
from app.agents.hume import HumeanAgent
from app.agents.kierkegaard import KierkegaardianAgent
from app.agents.jung import JungianAgent
from app.agents.kant import KantianAgent
from app.agents.marx import MarxistAgent
from app.agents.nagarjuna import MadhyamakaAgent
from app.agents.nietzsche import NietzscheanAgent
from app.agents.pragmatist import PragmatistAgent
from app.agents.spinoza import SpinozistAgent
from app.agents.weil import WeilianAgent
from app.agents.wittgenstein import WittgensteinianAgent

# Each is here for a test none of the others makes: genealogy, symbolic
# compensation, the four causes, impressions and the is/ought gap, conditions
# of possibility, grammatical dissolution, practical consequences, purpose
# over cause.
ARCHETYPE_MAP = {
    "nietzschean": NietzscheanAgent,
    "jungian": JungianAgent,
    "aristotelian": AristotelianAgent,
    "humean": HumeanAgent,
    "kantian": KantianAgent,
    "wittgensteinian": WittgensteinianAgent,
    "pragmatist": PragmatistAgent,
    "adlerian": AdlerianAgent,
    "spinozist": SpinozistAgent,
    "dostoevskian": DostoevskianAgent,
    "madhyamaka": MadhyamakaAgent,
    "weilian": WeilianAgent,
    "marxist": MarxistAgent,
    "kierkegaardian": KierkegaardianAgent,
}

SEEDED_ARCHETYPES = list(ARCHETYPE_MAP)

# How many stay out of a debate to judge it. A debate cannot take every
# philosopher or there is nobody left who did not take part.
JURY_SIZE = 3

# Five debating leaves exactly three to judge, which is the whole roster
# accounted for. Fewer debating means the jury is actually sampled.
DEFAULT_ARCHETYPES = [
    "nietzschean",
    "humean",
    "kantian",
    "aristotelian",
    "jungian",
]


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
