"""Elo arithmetic.

Panel scores become pairwise results inside one debate, and each pair moves
the rating. Every pair resolves against the ratings held BEFORE the debate,
so the order pairs are processed in cannot change the outcome.
"""

from app.core.jury import STARTING_ELO, compute_elo_updates


def test_ranked_scores_move_ratings_in_order():
    new = compute_elo_updates(
        {"A": 1500.0, "B": 1500.0, "C": 1500.0},
        {"A": 90.0, "B": 60.0, "C": 30.0},
    )
    assert new["A"] > new["B"] > new["C"]


def test_elo_is_zero_sum():
    """Nothing is created or destroyed: what one gains another loses."""
    before = {"A": 1500.0, "B": 1500.0, "C": 1500.0, "D": 1500.0}
    after = compute_elo_updates(before, {"A": 90.0, "B": 70.0, "C": 50.0, "D": 10.0})
    assert round(sum(after.values()), 2) == round(sum(before.values()), 2)


def test_beating_a_favourite_is_worth_more_than_beating_an_underdog():
    upset = compute_elo_updates({"fav": 1800.0, "dog": 1200.0}, {"fav": 50.0, "dog": 80.0})
    expected = compute_elo_updates({"fav": 1800.0, "dog": 1200.0}, {"fav": 80.0, "dog": 50.0})
    assert upset["dog"] - 1200.0 > 25          # the underdog gains a lot
    assert expected["fav"] - 1800.0 < 2        # the favourite gains almost nothing


def test_equal_scores_are_a_draw():
    assert compute_elo_updates({"A": 1500.0, "B": 1500.0}, {"A": 70.0, "B": 70.0}) == {
        "A": 1500.0,
        "B": 1500.0,
    }


def test_processing_order_does_not_change_the_outcome():
    ratings = {"A": 1600.0, "B": 1400.0, "C": 1500.0}
    scores = {"A": 80.0, "B": 60.0, "C": 70.0}
    assert compute_elo_updates(ratings, scores) == compute_elo_updates(
        dict(reversed(list(ratings.items()))), dict(reversed(list(scores.items())))
    )


def test_an_unrated_agent_starts_from_the_default():
    new = compute_elo_updates({}, {"A": 90.0, "B": 10.0})
    assert new["A"] > STARTING_ELO > new["B"]
