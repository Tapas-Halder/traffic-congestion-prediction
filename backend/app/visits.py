"""Approximate public dashboard visit counter.

Counts Streamlit browser sessions, not verified unique people. Only a UTC
timestamp is stored; no IP address, cookie or user-agent is stored by this table.
On ephemeral hosts the SQLite database can reset after redeployment. Set
VISITS_DB_PATH to a persistent-volume path if long-term totals are required.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

_DB_PATH = os.getenv("VISITS_DB_PATH", "visits.db")
_LOCK = threading.Lock()
_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _connect():
    path = Path(_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS visits ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, visited_at TEXT NOT NULL)"
    )
    return conn


def get_stats(now=None):
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(hours=24)).strftime(_FORMAT)
    conn = _connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        last_24h = conn.execute(
            "SELECT COUNT(*) FROM visits WHERE visited_at >= ?", (since,)
        ).fetchone()[0]
        first = conn.execute("SELECT MIN(visited_at) FROM visits").fetchone()[0]
        return {"total": total, "last_24h": last_24h, "first_visit_at": first}
    finally:
        conn.close()


def record_visit(now=None):
    now = now or datetime.now(timezone.utc)
    with _LOCK:
        conn = _connect()
        try:
            conn.execute("INSERT INTO visits (visited_at) VALUES (?)", (now.strftime(_FORMAT),))
            conn.commit()
        finally:
            conn.close()
    return get_stats(now)


def create_router():
    from fastapi import APIRouter, HTTPException

    router = APIRouter(prefix="/api/v1", tags=["visits"])

    @router.post("/visit")
    def post_visit():
        try:
            return record_visit()
        except sqlite3.Error as exc:
            raise HTTPException(
                status_code=503, detail="Visit counter storage is unavailable."
            ) from exc

    @router.get("/visits")
    def read_visits():
        try:
            return get_stats()
        except sqlite3.Error as exc:
            raise HTTPException(
                status_code=503, detail="Visit counter storage is unavailable."
            ) from exc

    return router
