"""Archivio locale (SQLite) di profili e pesate."""
import datetime
import pathlib
import sqlite3
import time

from paths import DATA_DIR

DB_PATH = DATA_DIR / "vibefit.db"


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
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                day TEXT NOT NULL,
                ts REAL NOT NULL,
                seconds INTEGER NOT NULL,
                points INTEGER NOT NULL,
                games INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS balance_tests (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                ts REAL NOT NULL,
                score_still REAL NOT NULL,
                score_follow REAL NOT NULL,
                balance_age REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self):
        """Aggiunge le colonne nate dopo la prima versione del database."""
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(scores)")}
        for name, ddl in (("seconds", "INTEGER NOT NULL DEFAULT 0"), ("kcal", "REAL NOT NULL DEFAULT 0")):
            if name not in cols:
                self.conn.execute(f"ALTER TABLE scores ADD COLUMN {name} {ddl}")
        self.conn.commit()

    # ---------- impostazioni ----------
    def get_setting(self, key, default=None):
        r = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r["value"] if r else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                          "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
        self.conn.commit()

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

    def add_score(self, pid, game, difficulty, score, medal, seconds=0, kcal=0.0):
        self.conn.execute(
            "INSERT INTO scores (profile_id, game, difficulty, score, medal, ts, seconds, kcal)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (pid, game, difficulty, score, medal, time.time(), seconds, kcal))
        self.conn.commit()

    def latest_weight(self, pid):
        r = self.conn.execute("SELECT kg FROM weights WHERE profile_id = ? ORDER BY ts DESC LIMIT 1",
                              (pid,)).fetchone()
        return r["kg"] if r else None

    def totals(self, pid):
        """Minuti, calorie e partite totali del profilo."""
        r = self.conn.execute(
            "SELECT COALESCE(SUM(seconds), 0) AS s, COALESCE(SUM(kcal), 0) AS k, COUNT(*) AS n"
            " FROM scores WHERE profile_id = ?", (pid,)).fetchone()
        return {"minutes": r["s"] / 60.0, "kcal": r["k"], "games": r["n"]}

    def minutes_by_day(self, pid, days=7):
        """Lista di (data, minuti) per gli ultimi `days` giorni, dal piu' vecchio a oggi."""
        today = datetime.date.today()
        out = []
        for i in range(days - 1, -1, -1):
            d = today - datetime.timedelta(days=i)
            start = datetime.datetime.combine(d, datetime.time.min).timestamp()
            r = self.conn.execute(
                "SELECT COALESCE(SUM(seconds), 0) FROM scores WHERE profile_id = ? AND ts >= ? AND ts < ?",
                (pid, start, start + 86400)).fetchone()
            out.append((d, r[0] / 60.0))
        return out

    def best_medals(self, pid):
        """{(gioco, difficolta'): medaglia migliore}."""
        return {(r["game"], r["difficulty"]): r["m"] for r in self.conn.execute(
            "SELECT game, difficulty, MAX(medal) AS m FROM scores WHERE profile_id = ? "
            "GROUP BY game, difficulty", (pid,))}

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

    def add_session(self, pid, seconds, points, games):
        self.conn.execute(
            "INSERT INTO sessions (profile_id, day, ts, seconds, points, games) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, datetime.date.today().isoformat(), time.time(), seconds, points, games))
        self.conn.commit()

    def trained_today(self, pid):
        r = self.conn.execute("SELECT COUNT(*) FROM sessions WHERE profile_id = ? AND day = ?",
                              (pid, datetime.date.today().isoformat())).fetchone()
        return r[0] > 0

    def streak(self, pid):
        """Giorni consecutivi di allenamento, contando da oggi (o da ieri se oggi non ancora fatto)."""
        days = {r[0] for r in self.conn.execute(
            "SELECT DISTINCT day FROM sessions WHERE profile_id = ?", (pid,))}
        d = datetime.date.today()
        if d.isoformat() not in days:
            d -= datetime.timedelta(days=1)
        n = 0
        while d.isoformat() in days:
            n += 1
            d -= datetime.timedelta(days=1)
        return n

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
