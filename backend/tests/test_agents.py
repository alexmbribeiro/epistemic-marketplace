"""The contract every agent has to meet.

An agent with no declared blind spot argues its corner forever and adds
nothing to a marketplace of positions — so the weakness is not decoration,
it is the thing that makes the roster work. These tests exist so a
philosopher cannot be added without one.
"""

import pytest

from app.agents import ARCHETYPE_MAP, DEFAULT_ARCHETYPES, JURY_SIZE, SEEDED_ARCHETYPES, build_agent

SEEDED = [(a, ARCHETYPE_MAP[a]()) for a in SEEDED_ARCHETYPES]


@pytest.mark.parametrize("archetype,agent", SEEDED, ids=[a for a, _ in SEEDED])
def test_every_agent_declares_where_its_method_fails(archetype, agent):
    assert "WEAKNESS TO EMBODY" in agent.system_prompt


@pytest.mark.parametrize("archetype,agent", SEEDED, ids=[a for a, _ in SEEDED])
def test_every_agent_says_what_its_own_number_measures(archetype, agent):
    """belief_score means something different to each of them by design; an
    agent that does not say what it means makes its number unreadable."""
    assert "belief_score" in agent.system_prompt


@pytest.mark.parametrize("archetype,agent", SEEDED, ids=[a for a, _ in SEEDED])
def test_every_agent_is_named_and_described(archetype, agent):
    assert agent.name and agent.name != "Base Agent"
    assert len(agent.description) > 40
    assert agent.archetype == archetype


def test_archetypes_are_unique():
    names = [a.name for _, a in SEEDED]
    assert len(set(names)) == len(names)


def test_the_default_roster_leaves_enough_agents_to_judge():
    """A debate cannot take everyone, or nobody is left who did not take part."""
    assert len(SEEDED_ARCHETYPES) - len(DEFAULT_ARCHETYPES) >= JURY_SIZE


def test_a_stored_persona_overrides_the_class():
    """A user-authored agent has no class; the record is its only persona, and
    without this it would debate with an empty system prompt."""
    agent = build_agent("some-new-school", "id-1", {}, "I am the stored prompt.", "Someone")
    assert agent.system_prompt == "I am the stored prompt."
    assert agent.name == "Someone"
    assert agent.archetype == "some-new-school"


def test_a_seeded_agent_keeps_its_own_prompt_when_none_is_stored():
    assert "Bayesian" not in build_agent("humean", "id-2", {}).system_prompt
    assert build_agent("humean", "id-2", {}).name == "Hume"
