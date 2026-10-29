"""LLM caching: InMemoryCache (RAM) vs SQLiteCache (file on disk) vs Off.

set_llm_cache() registers ONE global cache; LangChain checks it before every model call, so
repeating an identical prompt returns instantly and makes no new (paid) API request.
"""
import os
import sqlite3

from langchain_community.cache import SQLiteCache
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

from .config import SQLITE_PATH

_MEMORY_CACHE = InMemoryCache()  # module-level singleton so Streamlit reruns do not wipe it


def configure_cache(mode: str) -> None:
    if mode == "In-memory":
        set_llm_cache(_MEMORY_CACHE)
    elif mode == "SQLite":
        os.makedirs(os.path.dirname(SQLITE_PATH) or ".", exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=SQLITE_PATH))
    else:
        set_llm_cache(None)


def clear_cache(mode: str) -> None:
    if mode == "In-memory":
        _MEMORY_CACHE.clear()
    elif mode == "SQLite" and os.path.exists(SQLITE_PATH):
        SQLiteCache(database_path=SQLITE_PATH).clear()


def cache_info(mode: str) -> dict:
    """Small stats dict for the console tab."""
    info = {"mode": mode, "entries": 0, "location": "—", "survives_restart": False}
    try:
        if mode == "In-memory":
            info.update(entries=len(getattr(_MEMORY_CACHE, "_cache", {})), location="RAM (this process)")
        elif mode == "SQLite":
            info.update(location=SQLITE_PATH, survives_restart=True)
            if os.path.exists(SQLITE_PATH):
                with sqlite3.connect(SQLITE_PATH) as con:
                    info["entries"] = con.execute("SELECT COUNT(*) FROM full_llm_cache").fetchone()[0]
    except Exception:
        pass
    return info
