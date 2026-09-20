from app.agents.analogist import AnalogistAgent
from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.bayesian import BayesianAgent
from app.agents.contrarian import ContrarianAgent
from app.agents.dialectician import DialecticianAgent
from app.agents.domain_expert import DomainExpertAgent
from app.agents.falsificationist import FalsificationistAgent
from app.agents.frequentist import FrequentistAgent

ARCHETYPE_MAP = {
    "bayesian": BayesianAgent,
    "falsificationist": FalsificationistAgent,
    "analogist": AnalogistAgent,
    "contrarian": ContrarianAgent,
    "dialectician": DialecticianAgent,
    "frequentist": FrequentistAgent,
    "domain_expert": DomainExpertAgent,
}

DEFAULT_ARCHETYPES = [
    "bayesian",
    "falsificationist",
    "analogist",
    "contrarian",
    "dialectician",
    "frequentist",
]


def build_agent(archetype: str, agent_id: str, config: dict | None = None) -> BaseAgent:
    cls = ARCHETYPE_MAP.get(archetype, BaseAgent)
    return cls(agent_id=agent_id, config=config or {})
