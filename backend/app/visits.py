"""Approximate public dashboard visit counter.

If VISITS_GITHUB_TOKEN is configured, the aggregate count is stored in a
small JSON file on a dedicated GitHub data branch. No visitor identity,
IP address, cookie or user-agent is stored. SQLite remains available as a
local-development fallback.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

_DB_PATH = os.getenv("VISITS_DB_PATH", "visits.db")
_GITHUB_TOKEN = os.getenv("VISITS_GITHUB_TOKEN", "").strip()
_GITHUB_REPO = os.getenv("VISITS_GITHUB_REPO", "Tapas-Halder/traffic-congestion-prediction").strip()
_GITHUB_BRANCH = os.getenv("VISITS_GITHUB_BRANCH", "traffic-visit-data").strip()
_GITHUB_PATH = os.getenv("VISITS_GITHUB_PATH", "data/visits.json").strip()
_GITHUB_API = "https://api.github.com"
_LOCK = threading.Lock()
_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _now(now=None):
    return now or datetime.now(timezone.utc)


def _connect():
    path = Path(_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS visits ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, visited_at TEXT NOT NULL)"
    )
    return conn


def _github_headers():
    return {
        "Authorization": f"Bearer {_GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _github_read():
    url = f"{_GITHUB_API}/repos/{_GITHUB_REPO}/contents/{_GITHUB_PATH}"
    response = requests.get(
        url, headers=_github_headers(), params={"ref": _GITHUB_BRANCH}, timeout=12
    )
    if response.status_code == 404:
        return {"total": 0, "timestamps_last_24h": [], "first_visit_at": None}, None
    response.raise_for_status()
    payload = response.json()
    raw = base64.b64decode(payload["content"]).decode("utf-8")
    data = json.loads(raw)
    return data, payload["sha"]


def _github_write(data, sha):
    url = f"{_GITHUB_API}/repos/{_GITHUB_REPO}/contents/{_GITHUB_PATH}"
    encoded = base64.b64encode(
        json.dumps(data, indent=2).encode("utf-8")
    ).decode("ascii")
    body = {
        "message": "Update public project visit counter",
        "content": encoded,
        "branch": _GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha
    response = requests.put(url, headers=_github_headers(), json=body, timeout=12)
    response.raise_for_status()


def _github_stats(now=None):
    now = _now(now)
    data, _ = _github_read()
    cutoff = now - timedelta(hours=24)
    recent = []
    for value in data.get("timestamps_last_24h", []):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed >= cutoff:
                recent.append(value)
        except (TypeError, ValueError):
            continue
    return {
        "total": int(data.get("total", 0)),
        "last_24h": len(recent),
        "first_visit_at": data.get("first_visit_at"),
    }


def _github_record(now=None):
    now = _now(now)
    timestamp = now.strftime(_FORMAT)
    cutoff = now - timedelta(hours=24)
    for attempt in range(4):
        data, sha = _github_read()
        recent = []
        for value in data.get("timestamps_last_24h", []):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed >= cutoff:
                    recent.append(value)
            except (TypeError, ValueError):
                continue
        data["total"] = int(data.get("total", 0)) + 1
        data["timestamps_last_24h"] = recent + [timestamp]
        data["first_visit_at"] = data.get("first_visit_at") or timestamp
        try:
            _github_write(data, sha)
            return {
                "total": data["total"],
                "last_24h": len(data["timestamps_last_24h"]),
                "first_visit_at": data["first_visit_at"],
            }
        except requests.HTTPError as exc:
            # A concurrent request may have updated the same JSON file. Re-read
            # the latest SHA and retry instead of overwriting that newer commit.
            if exc.response is None or exc.response.status_code not in (409, 422) or attempt == 3:
                raise
    raise RuntimeError("Could not update the GitHub visit counter after retries.")


def get_stats(now=None):
    if _GITHUB_TOKEN:
        return _github_stats(now)
    now = _now(now)
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
    if _GITHUB_TOKEN:
        with _LOCK:
            return _github_record(now)
    now = _now(now)
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
        except (sqlite3.Error, requests.RequestException, ValueError, KeyError, RuntimeError) as exc:
            raise HTTPException(
                status_code=503, detail="Visit counter storage is unavailable."
            ) from exc

    @router.get("/visits")
    def read_visits():
        try:
            return get_stats()
        except (sqlite3.Error, requests.RequestException, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=503, detail="Visit counter storage is unavailable."
            ) from exc

    return router
