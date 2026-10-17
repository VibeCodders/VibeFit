import math

import pytest

from games import GAMES
from games.hula import Hula
from games.ice import IceBalance
from games.jump import Jump
from games.run import Run
from games.squat import Squat
from games.yoga import POSES, Yoga
from tests.conftest import run


@pytest.mark.parametrize("cls", GAMES)
@pytest.mark.parametrize("diff", [0, 1, 2])
def test_medal_thresholds_are_ordered(app, cls, diff):
    g = cls(app, diff)
    b, s, o = g.medals()
    assert 0 < b < s < o
    g.cleanup()


@pytest.mark.parametrize("cls", GAMES)
def test_every_game_runs_to_the_end_without_errors(app, cls):
    g = cls(app, 1)
    run(g, g.duration + 5, lambda t: {"x": 40 * math.sin(t * 2), "y": 20 * math.cos(t * 3)})
    assert g.done and g.score >= 0
    g.cleanup()


# ---------- Hula ----------
def circle(r, w):
    return lambda t: {"x": r * math.cos(w * t), "y": r * math.sin(w * t)}


def test_hula_counts_full_rotations(app):
    g = run(Hula(app, 1), 10, circle(40, 5.5))
    expected = 10 * 5.5 / (2 * math.pi)  # ~8.75 giri
    assert expected - 1.5 <= g.rotations <= expected + 0.5
    assert g.score > 0


def test_hula_ignores_tiny_movements_and_standing_still(app):
    assert run(Hula(app, 1), 10, circle(5, 5.5)).rotations == 0  # raggio sotto il minimo
    assert run(Hula(app, 1), 10, lambda t: {}).rotations == 0


def test_hula_counts_both_directions(app):
    assert run(Hula(app, 1), 10, circle(40, -5.5)).rotations >= 7


def test_hula_jitter_does_not_count(app):
    g = run(Hula(app, 1), 10, lambda t: {"x": 30 * math.sin(t * 20), "y": 0})  # avanti-indietro, non cerchio
    assert g.rotations <= 1


# ---------- Squat ----------
def squat_feed(cycles_from=2.0, period=3.0):
    def feed(t):
        if t < cycles_from:
            return {"total": 70}
        ph = (t - cycles_from) % period
        return {"total": 70 * (0.85 if ph < 1 else 1.15 if ph < 2 else 1.0)}
    return feed


def test_squat_counts_down_up_cycles(app):
    g = run(Squat(app, 1), 2.0 + 3 * 3.0 + 0.5, squat_feed())
    assert g.reps == 3 and g.score == 300


def test_squat_standing_still_scores_nothing(app):
    assert run(Squat(app, 1), 20, lambda t: {"total": 70}).reps == 0


def test_squat_small_wobble_is_ignored(app):
    g = run(Squat(app, 1), 20, lambda t: {"total": 70 * (1 + 0.02 * math.sin(t * 5))})
    assert g.reps == 0


# ---------- Salto ----------
def jump_feed(flight, every=2.5, start=2.5):
    def feed(t):
        ph = (t - start) % every
        return {"total": 2 if t > start and ph < flight else 70}
    return feed


def test_jump_height_from_flight_time(app):
    g = run(Jump(app, 1), 2.5 + 0.45 + 0.3, jump_feed(0.45))
    assert g.jumps == 1
    expected_cm = 9.81 * 0.45 ** 2 / 8 * 100  # ~24.8 cm
    assert abs(g.best - expected_cm) < 1.5
    assert abs(g.score - round(g.best * 10)) < 20


def test_jump_ignores_very_short_hops(app):
    assert run(Jump(app, 1), 12, jump_feed(0.08)).jumps == 0


def test_jump_ignores_sensor_dropouts_that_never_return(app):
    g = run(Jump(app, 1), 8, lambda t: {"total": 70 if t < 3 else 0})
    assert g.jumps == 0


# ---------- Corsa ----------
def test_run_counts_alternating_steps(app):
    g = run(Run(app, 1), 5, lambda t: {"x": 40 if int(t * 4) % 2 else -40})
    assert 16 <= g.steps <= 22
    assert g.py > 5


def test_run_without_alternation_counts_one_step(app):
    g = run(Run(app, 1), 5, lambda t: {"x": 40})
    assert g.steps <= 1


# ---------- Ghiaccio ----------
def test_ice_penguin_falls_with_constant_lean(app):
    g = run(IceBalance(app, 1), 30, lambda t: {"x": 150})
    assert g.lives < 3 or g.done


def test_ice_centered_keeps_lives(app):
    g = run(IceBalance(app, 1), 20, lambda t: {})
    assert g.lives == 3 and g.score == 0


# ---------- Yoga ----------
def test_yoga_full_score_when_on_target(app):
    def feed(t):
        i = min(int(t // 14), len(POSES) - 1)
        return {"x": POSES[i][1][0], "y": POSES[i][1][1]}
    g = run(Yoga(app, 1), Yoga.duration + 1, feed)
    assert g.score >= 950


def test_yoga_zero_when_far_from_target(app):
    g = run(Yoga(app, 1), Yoga.duration + 1, lambda t: {"x": 200, "y": 100})
    assert g.score == 0
