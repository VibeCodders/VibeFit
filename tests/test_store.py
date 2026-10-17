import datetime
import sqlite3
import time

import pytest

from db import Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "t.db")


def test_profiles_are_unique(store):
    store.add_profile("Anna", 170, 1990)
    with pytest.raises(sqlite3.IntegrityError):
        store.add_profile("Anna", 160, 1980)
    assert [p["name"] for p in store.list_profiles()] == ["Anna"]


def test_best_score_and_medal_per_difficulty(store):
    pid = store.add_profile("A", 170, 1990)
    store.add_score(pid, "squat", 1, 500, 1)
    store.add_score(pid, "squat", 1, 900, 2)
    store.add_score(pid, "squat", 2, 300, 0)
    assert store.best_score(pid, "squat", 1) == 900
    assert store.best_medal(pid, "squat", 1) == 2
    assert store.best_score(pid, "squat", 0) is None
    assert store.best_medals(pid)[("squat", 2)] == 0


def test_totals_and_calories(store):
    pid = store.add_profile("A", 170, 1990)
    store.add_score(pid, "run", 1, 100, 0, seconds=60, kcal=8.0)
    store.add_score(pid, "hula", 1, 100, 0, seconds=120, kcal=6.0)
    t = store.totals(pid)
    assert abs(t["minutes"] - 3.0) < 1e-9 and t["kcal"] == 14.0 and t["games"] == 2


def test_minutes_by_day_covers_last_week(store):
    pid = store.add_profile("A", 170, 1990)
    store.add_score(pid, "run", 1, 100, 0, seconds=600, kcal=1)
    days = store.minutes_by_day(pid, 7)
    assert len(days) == 7
    assert days[-1][0] == datetime.date.today() and abs(days[-1][1] - 10.0) < 1e-9
    assert all(m == 0 for _, m in days[:-1])


def test_streak_counts_consecutive_days(store):
    pid = store.add_profile("A", 170, 1990)
    today = datetime.date.today()
    for back in (0, 1, 2, 4):  # buco al terzo giorno indietro
        store.conn.execute("INSERT INTO sessions (profile_id, day, ts, seconds, points, games)"
                           " VALUES (?, ?, ?, 60, 10, 1)",
                           (pid, (today - datetime.timedelta(days=back)).isoformat(), time.time()))
    assert store.streak(pid) == 3


def test_streak_from_yesterday_when_not_trained_today(store):
    pid = store.add_profile("A", 170, 1990)
    y = datetime.date.today() - datetime.timedelta(days=1)
    store.conn.execute("INSERT INTO sessions (profile_id, day, ts, seconds, points, games)"
                       " VALUES (?, ?, ?, 60, 10, 1)", (pid, y.isoformat(), time.time()))
    assert store.streak(pid) == 1 and not store.trained_today(pid)


def test_settings_roundtrip(store):
    assert store.get_setting("x", "d") == "d"
    store.set_setting("x", 1)
    store.set_setting("x", 2)
    assert store.get_setting("x") == "2"


def test_migrates_old_scores_table(tmp_path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT UNIQUE, height_cm REAL, birth_year INTEGER);
        CREATE TABLE scores (id INTEGER PRIMARY KEY, profile_id INTEGER, game TEXT,
                             difficulty INTEGER, score INTEGER, medal INTEGER, ts REAL);
        INSERT INTO profiles VALUES (1, 'Old', 170, 1990);
        INSERT INTO scores VALUES (1, 1, 'ice', 1, 700, 1, 0);
    """)
    con.commit()
    con.close()
    s = Store(path)
    assert s.best_score(1, "ice", 1) == 700
    s.add_score(1, "ice", 1, 800, 2, seconds=30, kcal=2.0)  # le nuove colonne esistono
    assert s.totals(1)["games"] == 2
