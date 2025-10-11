#!/usr/bin/env python3
"""
COMPREHENSIVE FIXED search.py - Anti-LLM Rhyme Engine
Integrates k3/k2/k1 query architecture with all existing features preserved

KEY FIXES:
1. ✅ Three-stage k3/k2/k3 query approach (was: k2-only causing dollar/ART bug)
2. ✅ Proper phonetic scoring with score_rhyme() (was: no scoring)
3. ✅ Deduplication across query stages (was: duplicates)
4. ✅ Apostrophe filtering for garbage entries (was: contamination)
5. ✅ Limited queries to 2000 rows (was: 10000 causing overshoot)
6. ✅ Proper k3 extraction and usage (was: extracted but unused)

RECALL TARGET: 70-90% vs Datamuse (up from 21%)

PRESERVED FEATURES:
- Zipf band filtering for rarity
- Syllable and stress pattern filters
- Multiword phrase generation
- Tail distance slant ranking
- Datamuse fallback
- Comprehensive logging
- Thread-safe database operations
"""

from __future__ import annotations
import os
import sqlite3
import logging
import time
from typing import Any, Dict, List, Tuple, Optional, Set
from collections import defaultdict

from .data.paths import words_db
from .phonetics import parse_pron, k_keys, coda, meter_name, tail_distance, _is_vowel

# Initialize logger for this module
app_logger = logging.getLogger('UncommonRhymes.Search')

# =============================================================================
# DATABASE HELPERS - ENHANCED WITH K3 SUPPORT
# =============================================================================

def _con(path: str) -> sqlite3.Connection:
    """Create database connection with Row factory"""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con

def _get_word_data(word: str) -> Optional[Dict[str, Any]]:
    """
    Get complete word data from database including pronunciation and ALL keys (k1, k2, k3).
    This is the PRIMARY way to get pronunciation data.
    
    Returns dict with: word, pron, syls, stress, zipf, k1, k2, k3
    Returns None if word not found.
    """
    try:
        db_path = words_db()
        if not db_path.exists():
            app_logger.error(f"Database not found: {db_path}")
            return None
            
        with _con(str(db_path)) as con:
            # CRITICAL: Now includes k3 in SELECT statement
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
    """
    ENHANCED: Query words by rhyme keys with apostrophe filtering and proper limits.
    
    Args:
        key_conditions: List of key-based WHERE conditions (e.g., ["k3 = ?", "k2 != ?"])
        key_params: Parameters for key conditions
        common_where: Common filters (syllables, stress, etc.)
        common_params: Parameters for common filters
        order: ORDER BY clause
        limit: Maximum results (default 2000, was 10000)
    
    Returns:
        List of word dictionaries with full data including k3
    """
    try:
        # CRITICAL FIX: Filter out apostrophe words (garbage like "a.'m", "are'm", "don't", etc.)
        # These are malformed entries that contaminate results and cause poor recall
        apostrophe_filter = "word NOT LIKE \"%'%\""
        
        # Build complete WHERE clause
        all_conditions = key_conditions + [common_where, apostrophe_filter]
        where_clause = " AND ".join([c for c in all_conditions if c])
        
        # CRITICAL: Now includes k3 in SELECT statement
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
            # Check if table exists
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
    """
    ENHANCED: Enrich result with metadata and phonetic score.
    
    Args:
        r: Raw database row
        why: Reason string (e.g., "k3 perfect match")
        score: Phonetic similarity score (0.0-1.0)
    
    Returns:
        Enriched result dictionary
    """
    stress = r.get("stress") or ""
    return {
        "word": r.get("word",""),
        "syls": int(r.get("syls") or 0),
        "stress": stress,
        "meter": meter_name(stress),
        "zipf": r.get("zipf"),
        "pron": r.get("pron", ""),
        "why": why,
        "score": score,  # NEW: Include phonetic score
        "k1": r.get("k1", ""),  # NEW: Include keys for debugging
        "k2": r.get("k2", ""),
        "k3": r.get("k3", ""),
    }

# =============================================================================
# PHONETIC SCORING - NEW ADDITION
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
    
    Scoring hierarchy:
    - k3 match (stress-preserved): 1.00 (perfect)
    - k2 match (stress-agnostic): 0.85 (perfect by ear)
    - k1 match (vowel only): 0.35-0.59 (assonance)
    - Bonuses: alliteration (+0.10), multi-syllable (+0.05)
    
    Returns:
        (score, metadata_dict)
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
        
        # Calculate coda similarity for assonance
        target_coda = coda(target_phones)
        cand_coda = coda(candidate_phones)
        if target_coda or cand_coda:
            max_len = max(len(target_coda), len(cand_coda))
            if max_len > 0:
                distance = tail_distance(target_coda, candidate_phones)
                coda_sim = 1.0 - (distance / max_len)
                metadata['coda_similarity'] = coda_sim
                # Boost score based on coda similarity
                score += coda_sim * 0.24  # Up to 0.59 total for assonance
    
    # Alliteration bonus
    if target_phones and candidate_phones:
        # Extract onset consonants (before first vowel)
        target_onset = []
        for p in target_phones:
            if _is_vowel(p):
                break
            target_onset.append(p.rstrip('012'))  # Strip stress markers
        
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
    
    # Count matching syllables from the end
    matching_syls = 0
    for i in range(1, min(len(target_vowels), len(cand_vowels)) + 1):
        target_v = target_vowels[-i].rstrip('012')  # Compare vowel base only
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
# ENHANCED SELECTORS - K3/K2/K1 ARCHITECTURE
# =============================================================================

def _select_perfect_k3(
    target_k3: str,
    common_where: str,
    common_params: List[Any],
    zmin: float,
    zmax: float,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """
    STAGE 1: Select perfect rhymes using k3 (stress-preserved).
    This is the most strict match - same vowel, same coda, same stress pattern.
    
    Example: "dollar" matches "collar" (both k3="AA1|L ER0")
    """
    rows = _query_words_by_keys(
        key_conditions=["k3 = ?"],
        key_params=[target_k3],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000  # Query more, filter to limit after scoring
    )
    
    # Apply zipf band filtering
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
    """
    STAGE 2: Select near-perfect rhymes using k2 (stress-agnostic).
    Excludes k3 matches to avoid duplicates.
    
    These rhyme by ear but have different stress patterns.
    Example: "begin" (k2="IH|N") matches "within" (same k2, different k3)
    """
    rows = _query_words_by_keys(
        key_conditions=["k2 = ?", "k3 != ?"],
        key_params=[target_k2, target_k3],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    
    # Apply zipf band and exclude already-seen words
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
    """
    STAGE 3: Select assonance using k1 (vowel-only match).
    Excludes k2 matches to avoid duplicates.
    
    Same stressed vowel but different coda.
    Ranks by coda similarity for best slant rhymes.
    
    Example: "cat" (k1="AE") matches "sad" (same vowel, different coda)
    """
    rows = _query_words_by_keys(
        key_conditions=["k1 = ?", "k2 != ?"],
        key_params=[target_k1, target_k2],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    
    # Apply zipf band and exclude already-seen words
    rows = _zipf_band(rows, zmin, zmax)
    rows = [r for r in rows if r.get("word") not in exclude_k2_matches]
    
    # Rank by coda similarity (edit distance)
    SLANT_CODA_MAX = int(os.getenv("UR_SLANT_CODA_MAX", "1"))
    q_tail = coda(target_phones)
    
    scored: List[Tuple[float, int, Dict[str, Any]]] = []
    for r in rows:
        d = tail_distance(q_tail, parse_pron(r.get("pron", "")))
        if d <= SLANT_CODA_MAX:
            z = float(r.get("zipf") or 0.0)
            scored.append((-z, d, r))  # Sort by zipf DESC, then distance ASC
    
    scored.sort(key=lambda t: (t[0], t[1]))
    return [r for _, __, r in scored[:limit]]

# =============================================================================
# MULTIWORD PHRASE GENERATION - PRESERVED WITH ENHANCEMENTS
# =============================================================================

# Simple stoplist for modifiers
STOP = {"a", "an", "the", "of", "to", "and", "in", "on", "for", "by", "at", "with", "from"}

def _multiword_from_cmu_strict(
    target_k2: str,
    target_k1: str,
    zmax_multi: float,
    zmin: float,
    max_items: int,
    min_each: int
) -> Tuple[List[Dict[str, Any]], int]:
    """
    PRESERVED: Generate multiword rhyming phrases.
    Uses k2 for head words, with k1 fallback if needed.
    
    Returns:
        (phrases, total_count)
    """
    MULTI_CODA_MAX = int(os.getenv("UR_MULTI_CODA_MAX", "0"))
    
    # Build common filters for multiword queries
    common_where = "word NOT LIKE \"%'%\""  # Apostrophe filter
    common_params = []
    
    # Heads: strict k2 first
    heads = _query_words_by_keys(
        key_conditions=["k2 = ?"],
        key_params=[target_k2],
        common_where=common_where,
        common_params=common_params,
        order="zipf DESC",
        limit=2000
    )
    heads = _zipf_band(heads, zmin, zmax_multi)
    
    # Fallback to k1 if starving (only if MULTI_CODA_MAX > 0)
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
            # Approximate query coda from first available head
            base = heads[0] if heads else k1_rows[0]
            q_tail = coda(parse_pron(base.get("pron", "")))
            for r in k1_rows:
                d = tail_distance(q_tail, parse_pron(r.get("pron", "")))
                if d <= MULTI_CODA_MAX:
                    heads.append(r)
    
    # Modifiers: frequent, short words
    mods = _query_words_by_keys(
        key_conditions=[],
        key_params=[],
        common_where="zipf >= 4.2 AND syls <= 2 AND word NOT LIKE \"%'%\"",
        common_params=[],
        order="zipf DESC",
        limit=800
    )
    mods = [m for m in mods if (m.get("word") or "").lower() not in STOP]
    
    # Generate phrases
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
                "score": 0.85,  # Default score for multiword
                "zipf": (float(m.get("zipf", 0)) + float(h.get("zipf", 0))) / 2,
            })
            
            seen.add(ph)
            if len(phrases) >= max_items:
                break
        
        if len(phrases) >= max_items:
            break
    
    return phrases[:max_items], len(phrases)

# =============================================================================
# MAIN SEARCH FUNCTION - COMPREHENSIVE FIXED VERSION
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
) -> Dict[str, Any]:
    """
    COMPREHENSIVE FIXED search with k3/k2/k1 architecture.
    
    Three-stage query approach:
    1. k3 queries for perfect rhymes (stress-preserved)
    2. k2 queries for near-perfect rhymes (stress-agnostic)  
    3. k1 queries for assonance (vowel-only)
    
    Each stage excludes results from previous stages to avoid duplicates.
    All results are scored by phonetic similarity.
    
    Args:
        term: Query word
        max_items: Maximum results per category
        zipf_min: Minimum zipf frequency (rarity floor)
        zipf_max: Maximum zipf frequency (rarity ceiling)
        zipf_max_multi: Maximum zipf for multiword phrases
        min_each: Minimum results before relaxing filters
        syl_filter: Syllable count filter ("Any", "1", "2", etc.)
        stress_filter: Stress pattern filter ("Any", "1-0", etc.)
        relax_rap: Enable relaxed fallback search
        include_rap: Include rap database results (placeholder)
    
    Returns:
        Dictionary with keys: uncommon, slant, multiword, rap_targets
        Each category contains list of enriched result dictionaries
    """
    start_time = time.time()
    
    q = (term or "").strip().lower()
    if not q:
        app_logger.debug("Empty query term")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    # STEP 1: Look up the word in database to get pronunciation
    app_logger.debug(f"Looking up pronunciation for '{q}'")
    word_data = _get_word_data(q)
    
    if not word_data:
        app_logger.warning(f"Word '{q}' not found in database")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    pron_str = word_data.get('pron')
    if not pron_str:
        app_logger.error(f"Word '{q}' has no pronunciation in database")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    app_logger.debug(f"Found pronunciation for '{q}': {pron_str}")
    
    # STEP 2: Parse the pronunciation string into phonemes
    q_phones = parse_pron(pron_str)
    
    if not q_phones:
        app_logger.error(f"Failed to parse pronunciation '{pron_str}' for '{q}'")
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}
    
    app_logger.debug(f"Parsed phonemes for '{q}': {q_phones}")
    
    # STEP 3: Extract ALL phonetic keys (k1, k2, k3)
    # Use pre-computed keys from database if available
    if 'k1' in word_data and 'k2' in word_data and 'k3' in word_data:
        k1 = word_data['k1']
        k2 = word_data['k2']
        k3 = word_data['k3']
        app_logger.debug(f"Using pre-computed keys: k1={k1}, k2={k2}, k3={k3}")
    else:
        # Compute keys if not in database
        keys = k_keys(q_phones)
        if isinstance(keys, (tuple, list)) and len(keys) >= 3:
            k1, k2, k3 = keys[0], keys[1], keys[2]
        elif isinstance(keys, (tuple, list)) and len(keys) >= 2:
            k1, k2 = keys[0], keys[1]
            k3 = k2  # Fallback
        else:
            k1 = k2 = k3 = str(keys) if keys else ""
        app_logger.debug(f"Computed phonetic keys: k1={k1}, k2={k2}, k3={k3}")
    
    # Build common filter conditions for all queries
    common_conditions = []
    common_params = []
    
    # Exclude query word itself
    common_conditions.append("word != ?")
    common_params.append(q)
    
    # Syllable filter
    if syl_filter != "Any":
        if syl_filter == "5+":
            common_conditions.append("syls >= 5")
        else:
            common_conditions.append("syls = ?")
            common_params.append(int(syl_filter))
    
    # Stress pattern filter
    if stress_filter != "Any":
        common_conditions.append("stress = ?")
        common_params.append(stress_filter)
    
    common_where = " AND ".join(common_conditions) if common_conditions else "1=1"
    
    # Configure zipf bands
    zipf_min = float(os.getenv("UR_UNCOMMON_ZIPF_MIN", str(zipf_min)))
    zmax = float(zipf_max)
    zmax_m = float(zipf_max_multi)
    min_req = int(min_each)
    
    # Track words across stages to prevent duplicates
    seen_words: Set[str] = set()
    seen_words.add(q)
    
    # ==========================================================================
    # STAGE 1: PERFECT RHYMES (k3 matches)
    # ==========================================================================
    app_logger.debug(f"Stage 1: Querying k3 perfect matches for '{q}'")
    
    perfect_rows = _select_perfect_k3(
        target_k3=k3,
        common_where=common_where,
        common_params=common_params,
        zmin=zipf_min,
        zmax=zmax,
        limit=max_items * 2  # Get extra for scoring
    )
    
    uncommon = []
    for r in perfect_rows:
        word = r.get("word", "")
        if word in seen_words:
            continue
        seen_words.add(word)
        
        # Calculate phonetic similarity score
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        # Only include if score meets threshold
        if score >= 0.85:  # Perfect rhyme threshold
            uncommon.append(_enrich(r, f"k3 perfect match (score={score:.2f})", score))
    
    # Sort by score DESC, then zipf DESC
    uncommon.sort(key=lambda x: (-x['score'], -(x['zipf'] if x['zipf'] is not None else 0)))
    uncommon = uncommon[:max_items]
    
    app_logger.debug(f"Found {len(uncommon)} k3 perfect rhymes for '{q}'")
    
    # ==========================================================================
    # STAGE 2: NEAR-PERFECT RHYMES (k2 matches excluding k3)
    # ==========================================================================
    app_logger.debug(f"Stage 2: Querying k2 near-perfect matches for '{q}'")
    
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
        
        # Calculate phonetic similarity score
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        # k2 matches should score 0.60-0.85 range (near-perfect slant)
        if score >= 0.60:
            # Add to uncommon if score is very high
            if score >= 0.85 and len(uncommon) < max_items:
                uncommon.append(_enrich(r, f"k2 perfect by ear (score={score:.2f})", score))
            else:
                slant.append(_enrich(r, f"k2 near-perfect (score={score:.2f})", score))
    
    app_logger.debug(f"Found {len(slant)} k2 near-perfect rhymes for '{q}'")
    
    # ==========================================================================
    # STAGE 3: ASSONANCE (k1 matches excluding k2)
    # ==========================================================================
    app_logger.debug(f"Stage 3: Querying k1 assonance matches for '{q}'")
    
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
        
        # Calculate phonetic similarity score
        cand_phones = parse_pron(r.get("pron", ""))
        score, metadata = calculate_phonetic_similarity(
            q_phones, cand_phones,
            k1, k2, k3,
            r.get("k1", ""), r.get("k2", ""), r.get("k3", "")
        )
        
        # k1 matches should score 0.35-0.59 range (assonance)
        if score >= 0.35:
            slant.append(_enrich(r, f"k1 assonance (score={score:.2f})", score))
    
    # Sort slant by score DESC, then zipf DESC
    slant.sort(key=lambda x: (-x['score'], -(x['zipf'] if x['zipf'] is not None else 0)))
    slant = slant[:max_items]
    
    app_logger.debug(f"Total slant rhymes: {len(slant)} for '{q}'")
    
    # ==========================================================================
    # STAGE 4: MULTIWORD PHRASES
    # ==========================================================================
    app_logger.debug(f"Stage 4: Generating multiword phrases for '{q}'")
    
    multiword, _total = _multiword_from_cmu_strict(
        target_k2=k2,
        target_k1=k1,
        zmax_multi=zmax_m,
        zmin=zipf_min,
        max_items=max_items,
        min_each=min_req
    )
    
    app_logger.debug(f"Found {len(multiword)} multiword phrases for '{q}'")
    
    # ==========================================================================
    # STAGE 5: RAP DATABASE (placeholder)
    # ==========================================================================
    rap_targets: List[Dict[str, Any]] = []
    if include_rap:
        # Placeholder for future rap database integration
        rap_targets = []
    
    # ==========================================================================
    # FALLBACK: Relaxed search if no results
    # ==========================================================================
    if not (uncommon or slant or multiword) and relax_rap:
        app_logger.warning(f"No results for '{q}' with strict filters, trying relaxed...")
        try:
            res2 = search_all_categories(
                term,
                max_items=max_items,
                relax_rap=False,  # Prevent infinite recursion
                include_rap=False,
                zipf_max=5.5,  # Widen zipf band
                min_each=max(6, min_req // 2),
                zipf_max_multi=7.0,
                syl_filter=syl_filter,
                stress_filter=stress_filter,
            )
            if isinstance(res2, dict) and any(res2.get(k) for k in ["uncommon", "slant", "multiword"]):
                app_logger.info(f"Relaxed search found results for '{q}'")
                return res2
        except Exception as e:
            app_logger.error(f"Relaxed search failed for '{q}': {e}")
        
        # Last resort: Datamuse API fallback
        try:
            from rhyme_core.providers import datamuse as dm
            app_logger.info(f"Attempting Datamuse fallback for '{q}'")
            rhy = [w["word"] for w in dm.related(term, "rhy", max_items=max_items)] if hasattr(dm, "related") else []
            nry = [w["word"] for w in getattr(dm, "near_rhymes", lambda t, max_items=20: [])(term, max_items=max_items)]
            if rhy or nry:
                app_logger.info(f"Datamuse fallback found {len(rhy)} perfect, {len(nry)} near rhymes")
                return {
                    "uncommon": rhy[:max_items],
                    "slant": nry[:max_items],
                    "multiword": [],
                    "rap_targets": []
                }
        except Exception as e:
            app_logger.error(f"Datamuse fallback failed for '{q}': {e}")
    
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