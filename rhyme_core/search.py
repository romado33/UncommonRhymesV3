#!/usr/bin/env python3
"""
COMPREHENSIVE FIXED search.py - Anti-LLM Rhyme Engine with Optional Datamuse
Integrates k3/k2/k1 query architecture with optional Datamuse supplementation

RECALL FIXES APPLIED:
1. ✅ Three-stage k3/k2/k1 query approach (preserved - already working)
2. ✅ Proper phonetic scoring with score_rhyme() (preserved)
3. ✅ Deduplication across query stages (preserved)
4. ✅ Apostrophe filtering for garbage entries (preserved)
5. ✅ Limited queries to 2000 rows (preserved)
6. ✅ Proper k3 extraction and usage (preserved)
7. ✅ NEW: Optional Datamuse supplementation for recall boost

RECALL TARGET: 70-90% vs Datamuse (up from 21%)

PRESERVED FEATURES:
- Zipf band filtering for rarity
- Syllable and stress pattern filters
- Multiword phrase generation
- Tail distance slant ranking
- Comprehensive logging
- Thread-safe database operations

NEW INTEGRATION:
- Optional Datamuse supplementation (use_datamuse_supplement parameter)
- Hybrid results when enabled (CMU primary, Datamuse supplements)
- Maintains all CMU-only functionality when disabled
"""

from __future__ import annotations
import os
import sqlite3
import logging
import time
import requests
from typing import Any, Dict, List, Tuple, Optional, Set
from collections import defaultdict

from .data.paths import words_db
from .phonetics import parse_pron, k_keys, coda, meter_name, tail_distance, _is_vowel

# Initialize logger for this module
app_logger = logging.getLogger('UncommonRhymes.Search')

# =============================================================================
# DATABASE HELPERS - ENHANCED WITH K3 SUPPORT (PRESERVED)
# =============================================================================

def _con(path: str) -> sqlite3.Connection:
    """Create database connection with Row factory"""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def _get_word_data(word: str) -> Optional[Dict[str, Any]]:
    """
    Get complete word data from database including pronunciation and ALL keys (k1, k2, k3).
    """
    try:
        db_path = words_db()
        if not db_path.exists():
            app_logger.error(f"Database not found: {db_path}")
            return None
            
        with _con(str(db_path)) as con:
            cursor = con.execute(
                "SELECT word, pron, syls, stress, zipf, k1, k2, k3 FROM words WHERE word = ? LIMIT 1",
                (word.lower().strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        app_logger.error(f"Failed to get word data for '{word}': {e}")
        return None

def _query_words_by_keys(
    key_conditions: List[str], 
    key_params: List[Any],
    common_where: str,
    common_params: List[Any],
    order: Optional[str] = "zipf DESC",
    limit: int = 2000
) -> List[Dict[str, Any]]:
    """Query words by rhyme keys with apostrophe filtering and proper limits"""
    try:
        apostrophe_filter = "word NOT LIKE \"%'%\""
        
        all_conditions = key_conditions + [common_where, apostrophe_filter]
        where_clause = " AND ".join([c for c in all_conditions if c])
        
        sql = f"""
            SELECT word, pron, syls, stress, zipf, k1, k2, k3 
            FROM words 
            WHERE {where_clause}
        """
        
        if order:
            sql += f" ORDER BY {order}"
        sql += f" LIMIT {int(limit)}"
        
        db_path = words_db()
        if not db_path.exists():
            app_logger.error(f"Database not found: {db_path}")
            return []
            
        with _con(str(db_path)) as con:
            cursor = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            if not cursor.fetchone():
                app_logger.error("Table 'words' not found in database")
                return []
            
            all_params = key_params + common_params
            return [dict(r) for r in con.execute(sql, all_params).fetchall()]
            
    except sqlite3.Error as e:
        app_logger.error(f"Database query failed: {e}")
        return []

def _zipf_band(rows: List[Dict[str, Any]], zmin: float, zmax: float) -> List[Dict[str, Any]]:
    """Filter rows by zipf frequency band"""
    out = []
    for r in rows:
        z = r.get("zipf")
        if z is None: 
            continue
        try:
            zf = float(z)
        except Exception:
            continue
        if zmin <= zf <= zmax:
            out.append(r)
    return out

def _enrich(r: Dict[str, Any], why: str, score: float = 0.0) -> Dict[str, Any]:
    """Enrich result with metadata and phonetic score"""
    stress = r.get("stress") or ""
    return {
        "word": r.get("word",""),
        "syls": int(r.get("syls") or 0),
        "stress": stress,
        "meter": meter_name(stress),
        "zipf": r.get("zipf"),
        "pron": r.get("pron", ""),
        "why": why,
        "score": score,
        "k1": r.get("k1", ""),
        "k2": r.get("k2", ""),
        "k3": r.get("k3", ""),
    }

# =============================================================================
# PHONETIC SCORING - PRESERVED
# =============================================================================

def calculate_phonetic_similarity(
    target_phones: List[str],
    candidate_phones: List[str],
    target_k1: str,
    target_k2: str,
    target_k3: str,
    cand_k1: str,
    cand_k2: str,
    cand_k3: str
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate phonetic similarity score between target and candidate.
    """
    score = 0.0
    metadata = {
        'has_alliteration': False,
        'matching_syllables': 0,
        'coda_similarity': 0.0,
        'subcategory': 'unknown',
        'meter': 'unknown'
    }
    
    # Base score from key matching
    if target_k3 and cand_k3 and target_k3 == cand_k3:
        score = 1.00  # Perfect rhyme with stress preserved
        metadata['subcategory'] = 'k3_perfect'
    elif target_k2 and cand_k2 and target_k2 == cand_k2:
        score = 0.85  # Perfect by ear (stress-agnostic)
        metadata['subcategory'] = 'k2_perfect'
    elif target_k1 and cand_k1 and target_k1 == cand_k1:
        score = 0.35  # Assonance base
        metadata['subcategory'] = 'k1_assonance'
        
        target_coda = coda(target_phones)
        cand_coda = coda(candidate_phones)
        if target_coda or cand_coda:
            max_len = max(len(target_coda), len(cand_coda))
            if max_len > 0:
                distance = tail_distance(target_coda, candidate_phones)
                coda_sim = 1.0 - (distance / max_len)
                metadata['coda_similarity'] = coda_sim
                score += coda_sim * 0.24
    
    # Alliteration bonus
    if target_phones and candidate_phones:
        target_onset = []
        for p in target_phones:
            if _is_vowel(p):
                break
            target_onset.append(p.rstrip('012'))
        
        cand_onset = []
        for p in candidate_phones:
            if _is_vowel(p):
                break
            cand_onset.append(p.rstrip('012'))
        
        if target_onset and cand_onset and target_onset[0] == cand_onset[0]:
            score += 0.10
            metadata['has_alliteration'] = True
    
    # Multi-syllable bonus
    target_vowels = [p for p in target_phones if _is_vowel(p)]
    cand_vowels = [p for p in candidate_phones if _is_vowel(p)]
    
    matching_syls = 0
    for i in range(1, min(len(target_vowels), len(cand_vowels)) + 1):
        target_v = target_vowels[-i].rstrip('012')
        cand_v = cand_vowels[-i].rstrip('012')
        if target_v == cand_v:
            matching_syls = i
        else:
            break
    
    metadata['matching_syllables'] = matching_syls
    if matching_syls >= 2:
        score += 0.05
    
    return score, metadata

# =============================================================================
# ENHANCED SELECTORS - K3/K2/K1 ARCHITECTURE (PRESERVED)
# =============================================================================

def _select_perfect_k3(
    target_k3: str,
    common_where: str,
    common_params: List[Any],
    zmin: float,
    zmax: float,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """STAGE 1: Select perfect rhymes using k3 (stress-preserved)"""
    rows = _query_words_by_keys(
        key_conditions=["k3 = ?"],
        key_params=[target_k3],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    
    rows = _zipf_band(rows, zmin, zmax)
    return rows[:limit]

def _select_near_perfect_k2(
    target_k2: str,
    target_k3: str,
    exclude_k3_matches: Set[str],
    common_where: str,
    common_params: List[Any],
    zmin: float,
    zmax: float,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """STAGE 2: Select near-perfect rhymes using k2 (stress-agnostic)"""
    rows = _query_words_by_keys(
        key_conditions=["k2 = ?", "k3 != ?"],
        key_params=[target_k2, target_k3],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    
    rows = _zipf_band(rows, zmin, zmax)
    rows = [r for r in rows if r.get("word") not in exclude_k3_matches]
    
    return rows[:limit]

def _select_assonance_k1(
    target_k1: str,
    target_k2: str,
    target_phones: List[str],
    exclude_k2_matches: Set[str],
    common_where: str,
    common_params: List[Any],
    zmin: float,
    zmax: float,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """STAGE 3: Select assonance using k1 (vowel-only match)"""
    rows = _query_words_by_keys(
        key_conditions=["k1 = ?", "k2 != ?"],
        key_params=[target_k1, target_k2],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    
    rows = _zipf_band(rows, zmin, zmax)
    rows = [r for r in rows if r.get("word") not in exclude_k2_matches]
    
    # Rank by coda similarity
    SLANT_CODA_MAX = int(os.getenv("UR_SLANT_CODA_MAX", "1"))
    q_tail = coda(target_phones)
    
    scored: List[Tuple[float, int, Dict[str, Any]]] = []
    for r in rows:
        d = tail_distance(q_tail, parse_pron(r.get("pron", "")))
        if d <= SLANT_CODA_MAX:
            z = float(r.get("zipf") or 0.0)
            scored.append((-z, d, r))
    
    scored.sort(key=lambda t: (t[0], t[1]))
    return [r for _, __, r in scored[:limit]]

# =============================================================================
# MULTIWORD PHRASE GENERATION - PRESERVED
# =============================================================================

STOP = {"a", "an", "the", "of", "to", "and", "in", "on", "for", "by", "at", "with", "from"}

def _multiword_from_cmu_strict(
    target_k2: str,
    target_k1: str,
    zmax_multi: float,
    zmin: float,
    max_items: int,
    min_each: int
) -> Tuple[List[Dict[str, Any]], int]:
    """Generate multiword rhyming phrases"""
    MULTI_CODA_MAX = int(os.getenv("UR_MULTI_CODA_MAX", "0"))
    
    common_where = "word NOT LIKE \"%'%\""
    common_params = []
    
    heads = _query_words_by_keys(
        key_conditions=["k2 = ?"],
        key_params=[target_k2],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    heads = _zipf_band(heads, zmin, zmax_multi)
    
    if len(heads) < min_each and MULTI_CODA_MAX > 0:
        k1_rows = _query_words_by_keys(
            key_conditions=["k1 = ?"],
            key_params=[target_k1],
            common_where=common_where,
            common_params=common_params,
            order="zipf DESC",
            limit=2000
        )
        k1_rows = _zipf_band(k1_rows, zmin, zmax_multi)
        
        if heads or k1_rows:
            base = heads[0] if heads else k1_rows[0]
            q_tail = coda(parse_pron(base.get("pron", "")))
            for r in k1_rows:
                d = tail_distance(q_tail, parse_pron(r.get("pron", "")))
                if d <= MULTI_CODA_MAX:
                    heads.append(r)
    
    mods = _query_words_by_keys(
        key_conditions=[],
        key_params=[],
        common_where="zipf >= 4.2 AND syls <= 2 AND word NOT LIKE \"%'%\"",
        common_params=[],
        order="zipf DESC",
        limit=800
    )
    mods = [m for m in mods if (m.get("word") or "").lower() not in STOP]
    
    phrases: List[Dict[str, Any]] = []
    seen = set()
    
    for h in heads:
        hw = (h.get("word") or "").strip()
        if not hw:
            continue
        h_syls = int(h.get("syls") or 0)
        h_str = h.get("stress", "") or ""
        
        for m in mods:
            mw = (m.get("word") or "").strip()
            if not mw:
                continue
            
            ph = f"{mw} {hw}"
            if ph in seen:
                continue
            
            syls = int(m.get("syls") or 0) + h_syls
            stress = f"{m.get('stress', '')}{h_str}"
            
            phrases.append({
                "word": ph,
                "syls": syls,
                "stress": stress,
                "meter": meter_name(stress),
                "why": "multiword (modifier + head: strict/near-perfect tail)",
                "score": 0.85,
                "zipf": (float(m.get("zipf", 0)) + float(h.get("zipf", 0))) / 2,
            })
            
            seen.add(ph)
            if len(phrases) >= max_items:
                break
        
        if len(phrases) >= max_items:
            break
    
    return phrases[:max_items], len(phrases)

# =============================================================================
# NEW: OPTIONAL DATAMUSE SUPPLEMENTATION
# =============================================================================

def fetch_datamuse_supplement(
    word: str,
    timeout: float = 2.0,
    max_results: int = 100
) -> Dict[str, List[str]]:
    """
    Optional Datamuse supplementation for recall boost.
    
    Queries rel_nry endpoint to capture phrases and words we might miss.
    This is OPTIONAL and only used when use_datamuse_supplement=True.
    
    Returns:
        {'near_rhymes': [...], 'phrases': [...]}
    """
    results = {
        'near_rhymes': [],
        'phrases': []
    }
    
    try:
        response = requests.get(
            'https://api.datamuse.com/words',
            params={'rel_nry': word, 'max': max_results},
            timeout=timeout
        )
        
        if response.status_code == 200:
            items = response.json()
            
            for item in items:
                word_text = item.get('word', '')
                if ' ' in word_text:
                    results['phrases'].append(word_text)
                else:
                    results['near_rhymes'].append(word_text)
                    
    except Exception as e:
        app_logger.warning(f"Datamuse supplementation failed: {e}")
    
    return results

def supplement_with_datamuse(
    cmu_results: Dict[str, Any],
    target_word: str,
    datamuse_results: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Add Datamuse results to CMU results (supplement, don't replace).
    
    Only adds words that aren't already in CMU results.
    """
    # Extract all words already in CMU results
    seen_words = set()
    for word_list in [cmu_results.get('uncommon', []), 
                      cmu_results.get('slant', []),
                      cmu_results.get('multiword', [])]:
        for item in word_list:
            if isinstance(item, dict) and 'word' in item:
                seen_words.add(item['word'].lower())
            elif isinstance(item, str):
                seen_words.add(item.lower())
    
    # Add unseen near rhymes to slant
    for word in datamuse_results.get('near_rhymes', []):
        if word.lower() not in seen_words and word.lower() != target_word.lower():
            cmu_results['slant'].append({
                'word': word,
                'syls': 0,
                'stress': '',
                'meter': 'unknown',
                'zipf': 3.0,
                'pron': '',
                'why': 'datamuse near-rhyme supplement',
                'score': 0.65,
                'datamuse_supplemented': True
            })
            seen_words.add(word.lower())
    
    # Add unseen phrases to multiword
    for phrase in datamuse_results.get('phrases', []):
        if phrase.lower() not in seen_words:
            cmu_results['multiword'].append({
                'word': phrase,
                'syls': 0,
                'stress': '',
                'meter': 'unknown',
                'zipf': 3.5,
                'why': 'datamuse phrase supplement',
                'score': 0.80,
                'datamuse_supplemented': True
            })
            seen_words.add(phrase.lower())
    
    return cmu_results

# =============================================================================
# MAIN SEARCH FUNCTION - WITH OPTIONAL DATAMUSE SUPPLEMENTATION
# =============================================================================

def search_all_categories(
    term: str,
    max_items: int = 20,
    relax_rap: bool = True,
    include_rap: bool = False,
    zipf_min: float = 2.5,
    zipf_max: float = 4.0,
    min_each: int = 10,
    zipf_max_multi: float = 5.5,
    syl_filter: str = "Any",
    stress_filter: str = "Any",
    use_datamuse_supplement: bool = False,  # NEW: Optional supplementation
) -> Dict[str, Any]:
    """
    COMPREHENSIVE FIXED search with k3/k2/k1 architecture + optional Datamuse.
    
    Three-stage CMU query approach (PRESERVED):
    1. k3 queries for perfect rhymes (stress-preserved)
    2. k2 queries for near-perfect rhymes (stress-agnostic)  
    3. k1 queries for assonance (vowel-only)
    
    NEW: Optional Datamuse supplementation (use_datamuse_supplement=True):
    - Supplements CMU results with phrases and near-rhymes
    - Maintains CMU results as primary
    - Only adds words not already in CMU results
    
    Args:
        term: Query word
        max_items: Maximum results per category
        zipf_min: Minimum zipf frequency
        zipf_max: Maximum zipf frequency
        zipf_max_multi: Maximum zipf for multiword
        min_each: Minimum results before relaxing
        syl_filter: Syllable count filter
        stress_filter: Stress pattern filter
        relax_rap: Enable relaxed fallback
        include_rap: Include rap database
        use_datamuse_supplement: NEW - Enable Datamuse supplementation
    
    Returns:
        Dictionary with keys: uncommon, slant, multiword, rap_targets
    """
    start_time = time.time()
    
    q = (term or "").strip().lower()
    if not q:
        app_logger.debug("Empty query term")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    # STEP 1: Look up word and get pronunciation
    app_logger.debug(f"Looking up pronunciation for '{q}'")
    word_data = _get_word_data(q)
    
    if not word_data:
        app_logger.warning(f"Word '{q}' not found in database")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    pron_str = word_data.get('pron')
    if not pron_str:
        app_logger.error(f"Word '{q}' has no pronunciation")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    app_logger.debug(f"Found pronunciation for '{q}': {pron_str}")
    
    # STEP 2: Parse pronunciation
    q_phones = parse_pron(pron_str)
    
    if not q_phones:
        app_logger.error(f"Failed to parse pronunciation '{pron_str}'")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    app_logger.debug(f"Parsed phonemes: {q_phones}")
    
    # STEP 3: Extract phonetic keys
    if 'k1' in word_data and 'k2' in word_data and 'k3' in word_data:
        k1 = word_data['k1']
        k2 = word_data['k2']
        k3 = word_data['k3']
        app_logger.debug(f"Using pre-computed keys: k1={k1}, k2={k2}, k3={k3}")
    else:
        keys = k_keys(q_phones)
        if isinstance(keys, (tuple, list)) and len(keys) >= 3:
            k1, k2, k3 = keys[0], keys[1], keys[2]
        elif isinstance(keys, (tuple, list)) and len(keys) >= 2:
            k1, k2 = keys[0], keys[1]
            k3 = k2
        else:
            k1 = k2 = k3 = str(keys) if keys else ""
        app_logger.debug(f"Computed keys: k1={k1}, k2={k2}, k3={k3}")
    
    # Build common filters
    common_conditions = []
    common_params = []
    
    common_conditions.append("word != ?")
    common_params.append(q)
    
    if syl_filter != "Any":
        if syl_filter == "5+":
            common_conditions.append("syls >= 5")
        else:
            common_conditions.append("syls = ?")
            common_params.append(int(syl_filter))
    
    if stress_filter != "Any":
        common_conditions.append("stress = ?")
        common_params.append(stress_filter)
    
    common_where = " AND ".join(common_conditions) if common_conditions else "1=1"
    
    # Configure zipf bands
    zipf_min = float(os.getenv("UR_UNCOMMON_ZIPF_MIN", str(zipf_min)))
    zmax = float(zipf_max)
    zmax_m = float(zipf_max_multi)
    min_req = int(min_each)
    
    # Track words to prevent duplicates
    seen_words: Set[str] = set()
    seen_words.add(q)
    
    # ==========================================================================
    # STAGE 1: PERFECT RHYMES (k3 matches)
    # ==========================================================================
    app_logger.debug(f"Stage 1: Querying k3 perfect matches")
    
    perfect_rows = _select_perfect_k3(
        target_k3=k3,
        common_where=common_where,
        common_params=common_params,
        zmin=zipf_min,
        zmax=zmax,
        limit=max_items * 2
    )
    
    uncommon = []
    for r in perfect_rows:
        word = r.get("word", "")
        if word in seen_words:
            continue
        seen_words.add(word)
        
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        if score >= 0.85:
            uncommon.append(_enrich(r, f"k3 perfect match (score={score:.2f})", score))
    
    uncommon.sort(key=lambda x: (-x['score'], -(x['zipf'] if x['zipf'] is not None else 0)))
    uncommon = uncommon[:max_items]
    
    app_logger.debug(f"Found {len(uncommon)} k3 perfect rhymes")
    
    # ==========================================================================
    # STAGE 2: NEAR-PERFECT RHYMES (k2 matches excluding k3)
    # ==========================================================================
    app_logger.debug(f"Stage 2: Querying k2 near-perfect matches")
    
    near_perfect_rows = _select_near_perfect_k2(
        target_k2=k2,
        target_k3=k3,
        exclude_k3_matches=seen_words,
        common_where=common_where,
        common_params=common_params,
        zmin=zipf_min,
        zmax=zmax,
        limit=max_items * 2
    )
    
    slant = []
    for r in near_perfect_rows:
        word = r.get("word", "")
        if word in seen_words:
            continue
        seen_words.add(word)
        
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        if score >= 0.60:
            if score >= 0.85 and len(uncommon) < max_items:
                uncommon.append(_enrich(r, f"k2 perfect by ear (score={score:.2f})", score))
            else:
                slant.append(_enrich(r, f"k2 near-perfect (score={score:.2f})", score))
    
    app_logger.debug(f"Found {len(slant)} k2 near-perfect rhymes")
    
    # ==========================================================================
    # STAGE 3: ASSONANCE (k1 matches excluding k2)
    # ==========================================================================
    app_logger.debug(f"Stage 3: Querying k1 assonance matches")
    
    assonance_rows = _select_assonance_k1(
        target_k1=k1,
        target_k2=k2,
        target_phones=q_phones,
        exclude_k2_matches=seen_words,
        common_where=common_where,
        common_params=common_params,
        zmin=zipf_min,
        zmax=zmax,
        limit=max_items * 2
    )
    
    for r in assonance_rows:
        word = r.get("word", "")
        if word in seen_words:
            continue
        seen_words.add(word)
        
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        if score >= 0.35:
            slant.append(_enrich(r, f"k1 assonance (score={score:.2f})", score))
    
    slant.sort(key=lambda x: (-x['score'], -(x['zipf'] if x['zipf'] is not None else 0)))
    slant = slant[:max_items]
    
    app_logger.debug(f"Total slant rhymes: {len(slant)}")
    
    # ==========================================================================
    # STAGE 4: MULTIWORD PHRASES
    # ==========================================================================
    app_logger.debug(f"Stage 4: Generating multiword phrases")
    
    multiword, _total = _multiword_from_cmu_strict(
        target_k2=k2,
        target_k1=k1,
        zmax_multi=zmax_m,
        zmin=zipf_min,
        max_items=max_items,
        min_each=min_req
    )
    
    app_logger.debug(f"Found {len(multiword)} multiword phrases")
    
    # ==========================================================================
    # STAGE 5: RAP DATABASE (placeholder)
    # ==========================================================================
    rap_targets: List[Dict[str, Any]] = []
    if include_rap:
        rap_targets = []
    
    # ==========================================================================
    # NEW: OPTIONAL DATAMUSE SUPPLEMENTATION
    # ==========================================================================
    if use_datamuse_supplement:
        app_logger.info(f"Supplementing with Datamuse for '{q}'")
        datamuse_results = fetch_datamuse_supplement(q, timeout=2.0, max_results=100)
        
        # Create results dict for supplementation
        results = {
            'uncommon': uncommon,
            'slant': slant,
            'multiword': multiword,
            'rap_targets': rap_targets
        }
        
        # Supplement
        results = supplement_with_datamuse(results, q, datamuse_results)
        
        # Extract back
        uncommon = results['uncommon']
        slant = results['slant']
        multiword = results['multiword']
        
        app_logger.info(f"After Datamuse: {len(uncommon)} perfect, {len(slant)} slant, {len(multiword)} multiword")
    
    # ==========================================================================
    # FALLBACK: Relaxed search if no results
    # ==========================================================================
    if not (uncommon or slant or multiword) and relax_rap:
        app_logger.warning(f"No results for '{q}', trying relaxed...")
        try:
            res2 = search_all_categories(
                term,
                max_items=max_items,
                relax_rap=False,
                include_rap=False,
                zipf_max=5.5,
                min_each=max(6, min_req // 2),
                zipf_max_multi=7.0,
                syl_filter=syl_filter,
                stress_filter=stress_filter,
                use_datamuse_supplement=use_datamuse_supplement
            )
            if isinstance(res2, dict) and any(res2.get(k) for k in ["uncommon", "slant", "multiword"]):
                app_logger.info(f"Relaxed search found results")
                return res2
        except Exception as e:
            app_logger.error(f"Relaxed search failed: {e}")
    
    # ==========================================================================
    # RETURN RESULTS
    # ==========================================================================
    elapsed_ms = (time.time() - start_time) * 1000
    
    app_logger.info(
        f"Search completed for '{q}' in {elapsed_ms:.1f}ms: "
        f"{len(uncommon)} perfect, {len(slant)} slant, {len(multiword)} multiword"
    )
    
    return {
        "uncommon": uncommon[:max_items],
        "slant": slant[:max_items],
        "multiword": multiword[:max_items],
        "rap_targets": rap_targets[:max_items],
    }

# =============================================================================
# COMPATIBILITY LAYER FOR LEGACY IMPORTS
# =============================================================================

def search_rhymes(
    term: str,
    syl_filter: str = "Any",
    stress_filter: str = "Any",
    use_datamuse: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Compatibility wrapper for legacy code.
    
    DEPRECATED: New code should use search_all_categories directly.
    """
    return search_all_categories(
        term=term,
        syl_filter=syl_filter,
        stress_filter=stress_filter,
        use_datamuse_supplement=use_datamuse,  # Map to new parameter
        **kwargs
    )


# Export both old and new names for compatibility
__all__ = [
    'search_all_categories',
    'search_rhymes',
    'calculate_phonetic_similarity',
]