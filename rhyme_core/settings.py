# rhyme_core/settings.py
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any, Dict

SETTINGS_PATH = Path(os.getenv("UR_SETTINGS_PATH", "data/dev/settings.json"))

DEFAULTS: Dict[str, Any] = {
    # thresholds / tunables
    "zipf_max_perfect_slant": 4.0,
    "zipf_max_multi": 5.5,
    "min_each_bucket": 10,
    "slant_coda_max": 1,
    "multi_coda_max": 0,
    # integrations
    "use_datamuse": True,
    # LLM feature flags
    "features": {
        "llm_spellfix": False,
        "llm_query_normalizer": False,
        "llm_ranker": False,
        "llm_explanations": False,
        "llm_multiword_synth": False
    },
    # API keys (kept in-memory; not written unless you choose)
    "openai_api_key": os.getenv("OPENAI_API_KEY", "")
}

_state: Dict[str, Any] = {}

def _ensure_file():
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_PATH.exists():
        save(DEFAULTS)

def load() -> Dict[str, Any]:
    global _state
    _ensure_file()
    try:
        _state = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        _state = dict(DEFAULTS)
    # fill missing with defaults
    for k, v in DEFAULTS.items():
        if k not in _state:
            _state[k] = v if not isinstance(v, dict) else dict(v)
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                _state[k].setdefault(k2, v2)
    return _state

def save(new_state: Dict[str, Any] | None = None):
    global _state
    if new_state is not None:
        _state = new_state
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(_state, indent=2, ensure_ascii=False), encoding="utf-8")

def get(key: str, default=None):
    return _state.get(key, DEFAULTS.get(key, default))

def set(key: str, value: Any):
    _state[key] = value

def features() -> Dict[str, bool]:
    return _state.get("features", {})

def set_feature(name: str, on: bool):
    _state.setdefault("features", {})[name] = bool(on)

# Initialize once on import
load()
