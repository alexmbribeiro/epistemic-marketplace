"""Peer rating and Elo.

Three philosophers who did not take part read the debate and rate each
participant. The ratings become pairwise results, and those move an Elo.

The design decision that matters is what the judges score. Asking "who was
right" or "who was most convincing" would produce a popularity contest, and
with philosophers as judges it would mostly measure how many of the other
schools happen to be sympathetic to yours — Nietzsche will not be persuaded
by Kant no matter how well Kant reasons. So the criteria are deliberately
school-neutral and about craft: did the agent apply its OWN declared method
consistently, engage what was actually said, offer cruxes that could really
fail, and move when given reason to.

That does not remove judge bias, it only narrows it. Every rating is stored
with its judge, so the bias is measurable rather than invisible.
"""

import random

K_FACTOR = 32
STARTING_ELO = 1500.0

RATING_SCHEMA = {
    "type": "object",
    "properties": {
        "ratings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string", "description": "Exactly as given in the transcript"},
                    "method_fidelity": {"type": "integer", "description": "0-100. Did they reason the way their own stated method requires, or drift into generic argument?"},
                    "engagement": {"type": "integer", "description": "0-100. Did they address the actual claim and the actual challenges put to them, rather than a convenient version?"},
                    "crux_quality": {"type": "integer", "description": "0-100. Were their cruxes real conditions that could fail, or restatements of their position?"},
                    "responsiveness": {"type": "integer", "description": "0-100. Did they move when given reason, and hold when not? Both stubbornness and drift score low."},
                    "comment": {"type": "string", "description": "One sentence on the craft, not on whether you agree"},
                },
                "required": ["agent_name", "method_fidelity", "engagement", "crux_quality", "responsiveness", "comment"],
            },
        }
    },
    "required": ["ratings"],
}

JUDGE_PROMPT = """You are sitting as a judge on a debate you took no part in. You will be told \
which philosopher you are, and you should read as that philosopher — but you are scoring CRAFT, \
not agreement.

This is the whole discipline of the task: you will disagree with most of these agents, and that \
must not enter the scores. A philosopher whose conclusion you find wrong, or whose entire school \
you reject, can still reason impeccably by their own lights, and that is what earns a high score. \
An agent that reached a conclusion you like by sloppy means should score low.

Score each participant on four things, 0-100:

- method_fidelity: did they reason the way their own declared method requires? A Humean who
  appeals to necessity, or an Aristotelian who never defines a term, has broken their own rule.
- engagement: did they answer the claim as posed and the challenges as put, or a more convenient
  version of them?
- crux_quality: is what they said would change their mind a real condition that could actually
  fail, or a restatement of their position in the negative?
- responsiveness: did they move when given a reason, and hold firm when not given one? Score both
  the agent who never budges and the agent who drifts with the room equally low.

Use the full range. If everyone scores 70-80 you are not discriminating and the exercise is
worthless. Be willing to give a 25 and a 95 in the same debate."""


def select_jury(candidates: list, exclude_ids, size: int, seed=None, key=None) -> list:
    """Sample judges from those who did not take part.

    `key` maps a candidate to the identity compared against `exclude_ids`;
    it defaults to `.id` when present. Getting this wrong is silent and
    severe — comparing objects against a list of ids excludes nobody and the
    debate ends up judging itself — so the mismatch is guarded below.

    Returns fewer than `size` — possibly none — when the roster is too small.
    With eight philosophers and five debating there is exactly one possible
    jury, so "random" only bites for smaller debates.
    """
    if key is None:
        key = lambda c: getattr(c, "id", c)
    excluded = set(exclude_ids)
    eligible = [c for c in candidates if key(c) not in excluded]
    if excluded and len(eligible) == len(candidates):
        raise ValueError(
            "select_jury excluded nobody — exclude_ids does not match the candidates' keys"
        )
    rng = random.Random(seed)
    if len(eligible) <= size:
        return eligible
    return rng.sample(eligible, size)


def _expected(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def compute_elo_updates(current: dict[str, float], mean_scores: dict[str, float]) -> dict[str, float]:
    """Panel scores -> pairwise results -> new Elo.

    Elo is a pairwise system, so the panel has to be converted: within a
    debate, whoever scored higher beat whoever scored lower. Every pair is
    resolved against the ratings held BEFORE the debate, so the order the
    pairs are processed in cannot change the outcome.
    """
    names = sorted(mean_scores)
    deltas = {n: 0.0 for n in names}

    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra = current.get(a, STARTING_ELO)
            rb = current.get(b, STARTING_ELO)
            sa, sb = mean_scores[a], mean_scores[b]
            if abs(sa - sb) < 1e-9:
                outcome_a = 0.5
            else:
                outcome_a = 1.0 if sa > sb else 0.0
            expected_a = _expected(ra, rb)
            deltas[a] += K_FACTOR * (outcome_a - expected_a)
            deltas[b] += K_FACTOR * ((1.0 - outcome_a) - (1.0 - expected_a))

    return {n: round(current.get(n, STARTING_ELO) + deltas[n], 2) for n in names}


def summarise(ratings: list[dict]) -> dict:
    """Mean per participant across judges, plus the per-criterion breakdown."""
    per_agent: dict[str, list[dict]] = {}
    for r in ratings:
        per_agent.setdefault(r["agent_name"], []).append(r)

    out = {}
    for name, rows in per_agent.items():
        crit = {}
        for c in ("method_fidelity", "engagement", "crux_quality", "responsiveness"):
            crit[c] = round(sum(r[c] for r in rows) / len(rows), 1)
        out[name] = {
            "criteria": crit,
            "overall": round(sum(crit.values()) / len(crit), 1),
            "judges": len(rows),
            "comments": [{"judge": r.get("judge", ""), "comment": r["comment"]} for r in rows],
        }
    return out
