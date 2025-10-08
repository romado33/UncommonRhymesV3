# rhyme_core/llm.py
from __future__ import annotations
import os
from typing import Optional, List, Dict
from . import settings

def _enabled(flag: str) -> bool:
    return bool(settings.features().get(flag, False))

def maybe_spellfix(term: str) -> str:
    if not _enabled("llm_spellfix"):
        return term
    # placeholder: keep term unchanged; wire OpenAI later
    return term

def maybe_query_normalize(term: str) -> str:
    if not _enabled("llm_query_normalizer"):
        return term
    return term

def maybe_rank(results: List[Dict], bucket: str) -> List[Dict]:
    if not _enabled("llm_ranker"):
        return results
    # placeholder: no-op
    return results

def maybe_explain(pair: Dict) -> Optional[str]:
    if not _enabled("llm_explanations"):
        return None
    # placeholder explanation
    return f"LLM rationale: '{pair.get('word') or pair.get('target_word')}' relates to query."

def maybe_multiword_synth(heads: List[Dict]) -> List[str]:
    if not _enabled("llm_multiword_synth"):
        return []
    return []
