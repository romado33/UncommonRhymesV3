import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _candidate(p):
    if not p:
        return None
    P = Path(p)
    return P if P.exists() else None

def words_db() -> Path:
    p = _candidate(os.getenv("UR_WORDS_DB"))
    if p:
        return p
    if os.getenv("UR_USE_FULL_DB") == "1":
        p = _candidate(ROOT / "data" / "cache" / "words_index.full.sqlite")
        if p:
            return p
    return ROOT / "data" / "dev" / "words_index.sqlite"

def patterns_db() -> Path:
    p = _candidate(os.getenv("UR_PATTERNS_DB"))
    if p:
        return p
    if os.getenv("UR_USE_FULL_DB") == "1":
        p = _candidate(ROOT / "data" / "cache" / "patterns.full.sqlite")
        if p:
            return p
    return ROOT / "data" / "dev" / "patterns.sqlite"

def rap_db():
    # private DB; OK if missing
    return _candidate(os.getenv("UR_RAP_DB"))
