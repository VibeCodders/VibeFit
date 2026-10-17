"""Archivio locale (SQLite) di profili e pesate."""
import pathlib
import sqlite3
import time

DB_PATH = pathlib.Path(__file__).with_name("vibefit.db")


class Store:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                height_cm REAL NOT NULL,
                birth_year INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                ts REAL NOT NULL,
                kg REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                game TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                score INTEGER NOT NULL,
                medal INTEGER NOT NULL,
                ts REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS balance_tests (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                ts REAL NOT NULL,
                score_still REAL NOT NULL,
                score_follow REAL NOT NULL,
                balance_age REAL NOT NULL
            );
        """)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def list_profiles(self):
        return self.conn.execute("SELECT * FROM profiles ORDER BY name COLLATE NOCASE").fetchall()

    def add_profile(self, name, height_cm, birth_year):
        cur = self.conn.execute(
            "INSERT INTO profiles (name, height_cm, birth_year) VALUES (?, ?, ?)",
            (name, height_cm, birth_year))
        self.conn.commit()
        return cur.lastrowid

    def get_profile(self, pid):
        return self.conn.execute("SELECT * FROM profiles WHERE id = ?", (pid,)).fetchone()

    def add_weight(self, pid, kg):
        self.conn.execute("INSERT INTO weights (profile_id, ts, kg) VALUES (?, ?, ?)",
                          (pid, time.time(), kg))
        self.conn.commit()

    def add_score(self, pid, game, difficulty, score, medal):
        self.conn.execute(
            "INSERT INTO scores (profile_id, game, difficulty, score, medal, ts) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, game, difficulty, score, medal, time.time()))
        self.conn.commit()

    def best_score(self, pid, game, difficulty):
        r = self.conn.execute(
            "SELECT MAX(score) FROM scores WHERE profile_id = ? AND game = ? AND difficulty = ?",
            (pid, game, difficulty)).fetchone()
        return r[0]

    def best_medal(self, pid, game, difficulty):
        r = self.conn.execute(
            "SELECT MAX(medal) FROM scores WHERE profile_id = ? AND game = ? AND difficulty = ?",
            (pid, game, difficulty)).fetchone()
        return r[0] or 0

    def add_balance_test(self, pid, score_still, score_follow, balance_age):
        self.conn.execute(
            "INSERT INTO balance_tests (profile_id, ts, score_still, score_follow, balance_age)"
            " VALUES (?, ?, ?, ?, ?)", (pid, time.time(), score_still, score_follow, balance_age))
        self.conn.commit()

    def balance_tests(self, pid):
        return self.conn.execute(
            "SELECT ts, score_still, score_follow, balance_age FROM balance_tests"
            " WHERE profile_id = ? ORDER BY ts", (pid,)).fetchall()

    def weights(self, pid):
        return self.conn.execute(
            "SELECT ts, kg FROM weights WHERE profile_id = ? ORDER BY ts", (pid,)).fetchall()
