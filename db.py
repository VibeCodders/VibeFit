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

    def weights(self, pid):
        return self.conn.execute(
            "SELECT ts, kg FROM weights WHERE profile_id = ? ORDER BY ts", (pid,)).fetchall()
