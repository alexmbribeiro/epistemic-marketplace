"""What a debate's shape says about it.

Net shift is the wrong metric on its own: an agent that goes 0.65 -> 0.25 ->
0.70 nets to +0.05 and reads as anchored when it travelled further than
anyone. Swing measures the distance covered; reversed catches the agent that
went out and came back.
"""

from app.core.synthesis import build_trajectory, extract_exchanges, fallback_conclusion


class Position:
    def __init__(self, name, round_number, probability, challenges=None):
        self.agent_id = name
        self.agent_name = name
        self.archetype = name.lower()
        self.round_number = round_number
        self.probability_true = probability
        self.belief_score = probability
        self.challenges = challenges or []


def rounds(tracks):
    """tracks: {name: [r1, r2, r3]} -> the three rounds as the engine sees them."""
    return [
        [Position(name, r + 1, values[r]) for name, values in tracks.items()]
        for r in range(3)
    ]


def test_swing_measures_distance_travelled_not_net_change():
    t = build_trajectory(rounds({"Contrarian": [0.65, 0.25, 0.70]}))
    agent = t["agents"][0]
    assert abs(agent["shift"] - 0.05) < 1e-6      # net change is tiny
    assert abs(agent["swing"] - 0.85) < 1e-6      # distance covered is not


def test_an_out_and_back_move_is_flagged_as_reversed():
    t = build_trajectory(rounds({"Contrarian": [0.65, 0.25, 0.70]}))
    assert t["agents"][0]["reversed"] is True
    assert t["reversals"] == ["Contrarian"]


def test_a_small_wobble_is_not_a_reversal():
    """At a 5-point threshold every wobble counts, which buries the agent that
    genuinely swung 40."""
    t = build_trajectory(rounds({"Analogist": [0.55, 0.60, 0.55]}))
    assert t["agents"][0]["reversed"] is False


def test_a_monotonic_drift_is_movement_but_not_reversal():
    t = build_trajectory(rounds({"Hume": [0.50, 0.40, 0.30]}))
    agent = t["agents"][0]
    assert agent["moved"] is True
    assert agent["reversed"] is False


def test_an_immobile_agent_is_reported_as_anchored():
    t = build_trajectory(rounds({"Kant": [0.5, 0.5, 0.5]}))
    assert t["agents"][0]["swing"] == 0.0
    assert t["anchored"] == ["Kant"]


def test_the_biggest_mover_is_chosen_by_distance_not_net_change():
    t = build_trajectory(
        rounds({"Contrarian": [0.65, 0.25, 0.70], "Analogist": [0.55, 0.60, 0.65]})
    )
    assert t["biggest_mover"]["agent_name"] == "Contrarian"


def test_convergence_reads_the_spread_across_rounds():
    closing = build_trajectory(rounds({"A": [0.1, 0.3, 0.45], "B": [0.9, 0.7, 0.55]}))
    opening = build_trajectory(rounds({"A": [0.45, 0.3, 0.1], "B": [0.55, 0.7, 0.9]}))
    assert closing["convergence"] == "converged"
    assert opening["convergence"] == "diverged"


def test_exchanges_resolve_the_target_to_an_agent_name():
    """The model writes "the Kantian" as readily as "Kant"."""
    r = rounds({"Marx": [0.5, 0.5, 0.5], "Kant": [0.5, 0.5, 0.5]})
    r[1][0].challenges = [
        {"target_agent": "the Kantian", "challenge": "ignores material conditions", "type": "contradicts"}
    ]
    assert extract_exchanges(r)[0]["to_agent"] == "Kant"


def test_exchanges_drop_a_challenge_with_no_text():
    r = rounds({"Marx": [0.5, 0.5, 0.5], "Kant": [0.5, 0.5, 0.5]})
    r[1][0].challenges = [{"target_agent": "Kant", "challenge": "  ", "type": "contradicts"}]
    assert extract_exchanges(r) == []


def test_the_fallback_conclusion_only_claims_what_the_numbers_support():
    out = fallback_conclusion({"mean": 0.5, "std": 0.25, "disagreement_zone": "x"}, {"convergence": "diverged"})
    assert out["consensus"] == "deadlocked"
    assert out["generated"] is False
