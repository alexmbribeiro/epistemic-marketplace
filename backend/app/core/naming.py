"""Matching a name the model wrote against an actual agent.

Lives on its own because both the graph builder and the agents themselves
need it, and the graph builder already imports AgentResult from the agents
package — putting it there would close a cycle.
"""

import re


def _key(text: str) -> str:
    return re.sub(r"[^a-z]", "", (text or "").lower())


def resolve_agent(name: str, candidates) -> object | None:
    """Match a written name against an agent, by name or by archetype.

    Agents get named in whichever form the model reaches for: "Wittgenstein",
    "wittgensteinian", "the Kantian". An earlier version asked whether the
    written name appeared inside the label, which fails for every adjectival
    form — "wittgensteinian" is not a substring of "wittgenstein", it is
    longer — and silently dropped most of the challenges.

    Candidates may be objects (agent_name / name / archetype) or dicts
    (label / archetype).
    """
    want = _key(name)
    if not want:
        return None

    fallback = None
    for c in candidates:
        if isinstance(c, dict):
            raw_label = str(c.get("label", "")).split(" (")[0]
            raw_arche = str(c.get("archetype", ""))
        else:
            raw_label = getattr(c, "agent_name", None) or getattr(c, "name", "") or ""
            raw_arche = getattr(c, "archetype", "") or ""
        label, arche = _key(raw_label), _key(raw_arche)

        if want in (label, arche):
            return c
        # Containment both ways, so "wittgensteinian" finds Wittgenstein and
        # "the marxist" finds the marxist. Four characters minimum: shorter
        # fragments start matching things they should not.
        for form in (label, arche):
            if len(form) >= 4 and (form in want or want in form):
                fallback = fallback or c
    return fallback
