import math

import pytest

from games import GAMES
from games.dance import BEAT, LEAD_IN, PADS, Dance
from games.hula import Hula
from games.ice import IceBalance
from games.jump import Jump
from games.pearls import Pearls
from games.rope import Rope
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
    g = Yoga(app, 1)

    def feed(t):
        i = min(int(t // 14), len(g.order) - 1)
        return {"x": POSES[g.order[i]][1][0], "y": POSES[g.order[i]][1][1]}
    run(g, Yoga.duration + 1, feed)
    assert g.score >= 950


def test_yoga_picks_four_distinct_poses(app):
    g = Yoga(app, 1)
    assert len(g.order) == len(set(g.order)) == 4
    assert all(0 <= i < len(POSES) for i in g.order)


def test_yoga_zero_when_far_from_target(app):
    g = run(Yoga(app, 1), Yoga.duration + 1, lambda t: {"x": 200, "y": 100})
    assert g.score == 0


# ---------- Funambolo ----------
def test_rope_balances_when_leaning_toward_the_tilt(app):
    """Un 'giocatore' che sposta il peso dal lato della pendenza cammina senza cadere."""
    g = Rope(app, 1)

    def feed(t):
        return {"x": clamp_mm(g.a * 140)}

    run(g, 20, feed)
    assert g.lives == 3 and g.dist > 20


def clamp_mm(v):
    return max(-200.0, min(200.0, v))


def test_rope_falls_without_input(app):
    g = run(Rope(app, 2), 40, lambda t: {"x": 0})
    assert g.lives < 3 or g.done


# ---------- Pesca perle ----------
def test_pearls_penguin_follows_the_weight(app):
    g = run(Pearls(app, 1), 3, lambda t: {"x": 100, "y": 0})
    assert g.px > 5.0  # arrivato a destra


def test_pearls_collects_pearls_when_standing_on_them(app):
    g = Pearls(app, 0)
    inp_feed = lambda t: {}  # noqa: E731
    # mette il pinguino sopra la prima perla ogni frame
    t, dt = 0.0, 1 / 60
    import tests.conftest as c
    inp = c.make_input()
    while t < 15 and not g.done:
        if g.pearls:
            p = g.pearls[0]
            inp.x, inp.y = p["x"] / 6.2 * 100, p["y"] / 3.6 * 60
        g.tick(dt, inp)
        t += dt
    assert g.collected >= 4


def test_pearls_game_over_when_hit_repeatedly(app):
    g = Pearls(app, 2)  # difficile: 3 vite, 4 ricci
    for u in g.urchins:  # i ricci partono addosso al pinguino
        u["x"], u["y"], u["vx"], u["vy"] = 0.0, 0.0, 0.0, 0.0
    run(g, 20, lambda t: {})
    assert g.lives < 3


# ---------- Danza ----------
def dance_feed(g, perfect=True):
    def feed(t):
        for c in g.cues:
            if c["T"] - 0.1 <= t <= c["T"] + 0.1 and perfect:
                d = c["dir"]
                return {"x": {"left": -150, "right": 150}.get(d, 0), "y": {"front": 90, "back": -90}.get(d, 0)}
        return {"x": 0, "y": 0}
    return feed


def test_dance_hits_when_following_the_cues(app):
    g = Dance(app, 1)
    run(g, g.duration + 1, dance_feed(g))
    assert g.hits == g.n_cues and g.score >= g.medals()[2]


def test_dance_misses_when_standing_still(app):
    g = run(Dance(app, 1), 46, lambda t: {"x": 0, "y": 0})
    assert g.hits == 0 and g.score == 0


def test_dance_cues_are_on_the_beat_grid(app):
    g = Dance(app, 1)
    for c in g.cues:
        beats = (c["T"] - LEAD_IN) / BEAT
        assert abs(beats - round(beats)) < 1e-9
    assert all(c["dir"] in PADS for c in g.cues)
    assert all(a["dir"] != b["dir"] for a, b in zip(g.cues, g.cues[1:]))  # mai due volte di fila la stessa


# ---------- Taratura e robustezza ----------
def test_squat_ignores_sensor_noise(app):
    import random
    rnd = random.Random(3)

    def feed(t):
        base = 70 * (1 + (0.0 if t < 2 else (-0.15 if (t - 2) % 3 < 1 else 0.15 if (t - 2) % 3 < 2 else 0.0)))
        return {"total": base * (1 + rnd.uniform(-0.02, 0.02))}  # rumore +-2%
    g = run(Squat(app, 1), 2 + 3 * 3 + 0.5, feed)
    assert g.reps == 3


def test_squat_slow_weight_drift_is_not_a_rep(app):
    g = run(Squat(app, 1), 40, lambda t: {"total": 70 * (1 - 0.10 * t / 40)})  # cala del 10% in 40 s
    assert g.reps == 0


def test_jump_baseline_follows_slow_drift(app):
    def feed(t):
        w = 70 * (1 - 0.08 * min(t, 30) / 30)
        ph = (t - 35) % 2.5
        return {"total": 2 if t > 35 and ph < 0.45 else w}
    g = run(Jump(app, 1), 38.5, feed)
    assert g.jumps >= 1


def test_yoga_calibration_sets_targets_from_the_person(cal_app):
    g = Yoga(cal_app, 1)
    assert g.calib is not None

    def feed(t):
        return {"x": -90 if t < 5 else 90 if t < 10 else 0}
    run(g, 11, feed)
    assert g.calib is None
    assert abs(cal_app.shift - 81.0) < 3  # 90 mm * 0.9
    assert abs(g.shift - cal_app.shift) < 1e-9
    assert g.time_left > Yoga.duration - 2  # la calibrazione non ha consumato tempo di gioco


def test_yoga_uses_saved_calibration_without_asking(base):
    from tests.conftest import CalibratableApp
    app = CalibratableApp(base, shift=55.0)
    g = Yoga(app, 1)
    assert g.calib is None and g.shift == 55.0
    tree = next(i for i in range(len(POSES)) if POSES[i][2] == "tree")
    g.order[0] = tree
    g._set_pose(0)
    assert abs(abs(g.target[0]) - 55.0) < 1e-9


@pytest.mark.parametrize("cls", GAMES)
def test_standing_still_does_not_earn_a_medal(app, cls):
    """Nessun gioco deve regalare medaglie a chi sta fermo (a difficolta' normale)."""
    import random
    random.seed(7)
    g = run(cls(app, 1), cls.duration + 5, lambda t: {"x": 0.0, "y": 0.0})
    bronze = g.medals()[0]
    assert g.score < bronze, f"{cls.key}: {g.score} >= bronzo {bronze}"
