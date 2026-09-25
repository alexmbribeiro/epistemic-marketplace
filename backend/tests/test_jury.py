"""Drawing the jury.

Judges come from the philosophers who did not take part. Getting the
comparison wrong here is silent and severe: an early version compared
CognitiveAgent objects against a list of UUIDs, excluded nobody, and let an
agent score a debate it had argued in.
"""

import pytest

from app.core.jury import select_jury


class Agent:
    def __init__(self, id, name=""):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Agent({self.id})"


ROSTER = [Agent(i) for i in range(8)]


def test_participants_are_never_drawn():
    jury = select_jury(ROSTER, [0, 1, 2, 3], size=3, seed=1)
    assert all(a.id > 3 for a in jury)


def test_returns_the_requested_size_when_the_pool_allows():
    assert len(select_jury(ROSTER, [0, 1, 2], size=3, seed=1)) == 3


def test_returns_what_is_left_when_the_pool_is_too_small():
    """Five of eight debating leaves exactly three, so the draw is forced."""
    assert len(select_jury(ROSTER, [0, 1, 2, 3, 4], size=3, seed=1)) == 3
    assert len(select_jury(ROSTER, list(range(7)), size=3, seed=1)) == 1


def test_a_key_mismatch_raises_rather_than_excluding_nobody():
    """The bug that let Wittgenstein judge his own debate: exclusion ids that
    match nothing must be loud, because silently they exclude no one."""
    with pytest.raises(ValueError, match="excluded nobody"):
        select_jury(ROSTER, ["not-an-id"], size=3)


def test_the_draw_is_reproducible_for_a_given_seed():
    assert [a.id for a in select_jury(ROSTER, [0], size=3, seed=7)] == [
        a.id for a in select_jury(ROSTER, [0], size=3, seed=7)
    ]


def test_plain_values_work_as_candidates():
    assert set(select_jury(list("abcdefgh"), list("abcde"), size=3)) <= set("fgh")
