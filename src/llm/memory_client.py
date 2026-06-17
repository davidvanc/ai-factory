"""
Lokale memory store (SQLite) — vervangt de oude HTTP Memory Service op de Storage VM.

Houdt exact dezelfde interface als voorheen aan (add_project, add_lesson,
get_relevant_lessons, allocate_port, list_ports, get_stats), zodat de rest van
de pipeline ongewijzigd blijft werken. Geen netwerk, geen aparte VM nodig.

De database staat standaard in ./data/factory.db (override met env MEMORY_DB).
Memory mag de pipeline nooit doen falen: elke fout wordt gevangen en levert een
veilige default op (None / [] / fallback-poort).
"""
import os
import json
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Eenvoudige stopwoordenlijst voor relevantie-scoring van lessen.
_STOPWORDS = {
    "de", "het", "een", "en", "of", "die", "dat", "is", "te", "in", "op", "met",
    "voor", "van", "aan", "naar", "maak", "make", "service", "die", "doet", "the",
    "a", "an", "to", "of", "and", "or", "that", "with", "for", "create", "build",
}


def _tokens(text: str) -> set:
    return {
        w for w in re.split(r"[^a-z0-9]+", (text or "").lower())
        if len(w) > 2 and w not in _STOPWORDS
    }


class MemoryClient:
    # Eén lock per proces volstaat: de pipeline draait sequentieel.
    _lock = threading.Lock()

    def __init__(self):
        default_path = Path(__file__).resolve().parents[2] / "data" / "factory.db"
        self.db_path = Path(os.getenv("MEMORY_DB", str(default_path)))
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
        except Exception as e:
            print(f"[memory] init faalde (niet kritiek): {e}")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    task TEXT,
                    description TEXT,
                    status TEXT,
                    attempts INTEGER,
                    premium_used INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    category TEXT,
                    pattern TEXT,
                    fix TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    created_at TEXT,
                    UNIQUE(category, pattern)
                );
                CREATE TABLE IF NOT EXISTS ports (
                    project_name TEXT PRIMARY KEY,
                    port INTEGER UNIQUE,
                    created_at TEXT
                );
                """
            )

    # ------------------------------------------------------------------ projects
    def add_project(self, project_name: str, task: str, description: str,
                    status: str, attempts: int, premium_used: bool = False,
                    metadata: dict = None) -> Optional[int]:
        try:
            with self._lock, self._connect() as conn:
                cur = conn.execute(
                    """INSERT INTO projects
                       (project_name, task, description, status, attempts,
                        premium_used, metadata, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (project_name, task, description, status, int(attempts),
                     1 if premium_used else 0,
                     json.dumps(metadata, default=str) if metadata else None,
                     datetime.now().isoformat()),
                )
                return cur.lastrowid
        except Exception as e:
            print(f"[memory] add_project faalde: {e}")
            return None

    # ------------------------------------------------------------------- lessons
    def add_lesson(self, category: str, pattern: str, fix: str = None,
                   project_id: int = None) -> Optional[int]:
        try:
            with self._lock, self._connect() as conn:
                # Zelfde les nog eens gezien? Verhoog de teller i.p.v. dupliceren.
                row = conn.execute(
                    "SELECT id FROM lessons WHERE category = ? AND pattern = ?",
                    (category, pattern),
                ).fetchone()
                if row:
                    conn.execute(
                        """UPDATE lessons
                           SET occurrence_count = occurrence_count + 1,
                               fix = COALESCE(?, fix)
                           WHERE id = ?""",
                        (fix, row["id"]),
                    )
                    return row["id"]
                cur = conn.execute(
                    """INSERT INTO lessons
                       (project_id, category, pattern, fix, occurrence_count, created_at)
                       VALUES (?, ?, ?, ?, 1, ?)""",
                    (project_id, category, pattern, fix, datetime.now().isoformat()),
                )
                return cur.lastrowid
        except Exception as e:
            print(f"[memory] add_lesson faalde: {e}")
            return None

    def get_relevant_lessons(self, task: str, limit: int = 10) -> list:
        """Lessen gerangschikt op trefwoord-overlap met de taak, dan op frequentie."""
        try:
            task_tokens = _tokens(task)
            with self._lock, self._connect() as conn:
                rows = conn.execute(
                    "SELECT category, pattern, fix, occurrence_count FROM lessons"
                ).fetchall()

            scored = []
            for r in rows:
                overlap = len(task_tokens & _tokens(f"{r['category']} {r['pattern']}"))
                scored.append((overlap, r["occurrence_count"], dict(r)))

            # Hoogste overlap eerst; bij gelijke overlap de meest voorkomende les.
            scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

            # Als niets overlapt, val terug op de vaakst voorkomende lessen.
            return [item[2] for item in scored[:limit]]
        except Exception as e:
            print(f"[memory] get_relevant_lessons faalde: {e}")
            return []

    # --------------------------------------------------------------------- ports
    def allocate_port(self, project_name: str, start: int = 8001, end: int = 9000) -> int:
        """Reserveer (of haal op) een unieke poort voor een project. Fallback: 8000 bij fout."""
        try:
            with self._lock, self._connect() as conn:
                row = conn.execute(
                    "SELECT port FROM ports WHERE project_name = ?", (project_name,)
                ).fetchone()
                if row:
                    return row["port"]

                used = {
                    r["port"] for r in conn.execute("SELECT port FROM ports").fetchall()
                }
                for candidate in range(start, end + 1):
                    if candidate not in used:
                        conn.execute(
                            "INSERT INTO ports (project_name, port, created_at) VALUES (?, ?, ?)",
                            (project_name, candidate, datetime.now().isoformat()),
                        )
                        return candidate
            print("[memory] geen vrije poort in bereik, fallback naar 8000")
            return 8000
        except Exception as e:
            print(f"[memory] port allocate faalde, fallback naar 8000: {e}")
            return 8000

    def list_ports(self) -> list:
        try:
            with self._lock, self._connect() as conn:
                rows = conn.execute(
                    "SELECT project_name, port FROM ports ORDER BY port"
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[memory] list_ports faalde: {e}")
            return []

    # --------------------------------------------------------------------- stats
    def get_stats(self) -> Optional[dict]:
        try:
            with self._lock, self._connect() as conn:
                projects = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
                successes = conn.execute(
                    "SELECT COUNT(*) AS n FROM projects WHERE status = 'success'"
                ).fetchone()["n"]
                lessons = conn.execute("SELECT COUNT(*) AS n FROM lessons").fetchone()["n"]
                ports = conn.execute("SELECT COUNT(*) AS n FROM ports").fetchone()["n"]
            return {
                "projects": projects,
                "successes": successes,
                "failures": projects - successes,
                "lessons": lessons,
                "allocated_ports": ports,
                "db_path": str(self.db_path),
            }
        except Exception as e:
            print(f"[memory] get_stats faalde: {e}")
            return None
