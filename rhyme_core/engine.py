#!/usr/bin/env python3
"""
Anti-LLM Rhyme Engine - Complete Version
Merges all functionality from previous versions without losing features.
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import requests
from functools import lru_cache
import time
from collections import defaultdict

@dataclass
class Config:
    """Configuration for rhyme engine"""
    db_path: str = "rhyme.db"
    max_items: int = 30
    zipf_max_slant: float = 6.0
    datamuse_timeout: int = 3
    cache_ttl: int = 3600
    alliteration_bonus: float = 0.10
    multisyl_bonus: float = 0.05

cfg = Config()

# Cache for Datamuse results
_datamuse_cache: Dict[str, Tuple[Any, float]] = {}

# Meter patterns (from engine_hybrid.py)
METER_PATTERNS = {
    '0-1': 'iamb',
    '1-0': 'trochee', 
    '0-0-1': 'anapest',
    '1-0-0': 'dactyl',
    '0-1-0': 'amphibrach',
    '1-1': 'spondee',
    '0-0': 'pyrrhic',
    '1': 'stressed',
    '0': 'unstressed'
}

# Emoji indicators (from engine_hybrid.py)
EMOJI = {
    'k3_perfect': '⭐',
    'k2_perfect': '✓',
    'near_perfect': '🎯',
    'assonance': '≈',
    'fallback': '⚡',
    'multiword': '🔗',
    'datamuse': '✓',
    'technical': '📚',
    'alliteration': '🔤',
    'multisyl': '🎵'
}

def get_db():
    """Get database connection"""
    return sqlite3.connect(cfg.db_path)

def strip_stress(phoneme: str) -> str:
    """Remove stress markers (0, 1, 2) from phoneme"""
    return phoneme.rstrip('012')

def is_vowel(phoneme: str) -> bool:
    """Check if phoneme is a vowel (has stress marker)"""
    return phoneme and phoneme[-1] in '012'

def extract_stress_pattern(phonemes: List[str]) -> str:
    """Extract stress pattern for meter classification"""
    pattern = []
    for ph in phonemes:
        if is_vowel(ph):
            # Primary stress (1,2) = 1, no stress (0) = 0
            pattern.append('1' if ph[-1] in '12' else '0')
    return '-'.join(pattern) if pattern else ''

def get_meter_type(stress_pattern: str) -> str:
    """Classify meter type from stress pattern"""
    return METER_PATTERNS.get(stress_pattern, 'other')

def extract_vowels(phonemes: List[str]) -> List[str]:
    """Extract vowel phonemes for assonance analysis"""
    return [strip_stress(ph) for ph in phonemes if is_vowel(ph)]

def extract_consonants(phonemes: List[str]) -> List[str]:
    """Extract consonant phonemes for consonance analysis"""
    return [ph for ph in phonemes if not is_vowel(ph)]

def extract_onset(phonemes: List[str]) -> List[str]:
    """Extract onset consonants (before first vowel) for alliteration"""
    onset = []
    for ph in phonemes:
        if is_vowel(ph):
            break
        onset.append(strip_stress(ph))
    return onset

def calculate_coda_similarity(phonemes1: List[str], phonemes2: List[str]) -> float:
    """Calculate similarity of coda (consonants after nucleus)"""
    # Find last stressed vowel position
    def get_coda(phonemes):
        coda = []
        last_stressed = -1
        for i, ph in enumerate(phonemes):
            if ph[-1] in '12':  # Primary/secondary stress
                last_stressed = i
        if last_stressed >= 0 and last_stressed < len(phonemes) - 1:
            coda = phonemes[last_stressed + 1:]
        return [strip_stress(p) for p in coda if not is_vowel(p)]
    
    coda1 = set(get_coda(phonemes1))
    coda2 = set(get_coda(phonemes2))
    
    if not coda1 and not coda2:
        return 1.0
    
    intersection = len(coda1 & coda2)
    union = len(coda1 | coda2)
    
    return intersection / union if union > 0 else 0.0

def count_matching_syllables(phonemes1: List[str], phonemes2: List[str]) -> int:
    """Count matching syllables from the end (for multi-syllable rhymes)"""
    def get_syllables(phonemes):
        syllables = []
        current_syl = []
        for ph in phonemes:
            current_syl.append(ph)
            if is_vowel(ph):
                syllables.append(current_syl)
                current_syl = []
        if current_syl and syllables:
            syllables[-1].extend(current_syl)
        return syllables
    
    syl1 = get_syllables(phonemes1)
    syl2 = get_syllables(phonemes2)
    
    matches = 0
    for s1, s2 in zip(reversed(syl1), reversed(syl2)):
        s1_base = [strip_stress(p) for p in s1]
        s2_base = [strip_stress(p) for p in s2]
        if s1_base == s2_base:
            matches += 1
        else:
            break
    
    return matches

def calculate_phonetic_similarity(phonemes1: List[str], phonemes2: List[str]) -> float:
    """Calculate overall phonetic similarity"""
    p1_base = [strip_stress(ph) for ph in phonemes1]
    p2_base = [strip_stress(ph) for ph in phonemes2]
    
    matches = sum(1 for a, b in zip(p1_base, p2_base) if a == b)
    max_len = max(len(p1_base), len(p2_base))
    
    return matches / max_len if max_len > 0 else 0.0

def query_datamuse(term: str) -> Dict[str, Any]:
    """Query Datamuse API for rhymes"""
    cache_key = term.lower()
    if cache_key in _datamuse_cache:
        cached_result, timestamp = _datamuse_cache[cache_key]
        if time.time() - timestamp < cfg.cache_ttl:
            return cached_result
    
    try:
        url = f"https://api.datamuse.com/words?rel_nry={term}&max=100"
        response = requests.get(url, timeout=cfg.datamuse_timeout)
        response.raise_for_status()
        
        results = response.json()
        single_words = []
        multi_words = []
        all_words = set()
        
        for item in results:
            word = item.get('word', '').lower()
            if not word:
                continue
                
            all_words.add(word)
            
            if ' ' in word:
                multi_words.append({
                    'word': word,
                    'score': item.get('score', 0)
                })
            else:
                single_words.append({
                    'word': word,
                    'score': item.get('score', 0)
                })
        
        result = {
            'single': single_words,
            'multi': multi_words,
            'all_words': all_words
        }
        
        _datamuse_cache[cache_key] = (result, time.time())
        return result
        
    except Exception as e:
        print(f"Datamuse API error: {e}")
        return {'single': [], 'multi': [], 'all_words': set()}

def get_word_pronunciation(term: str) -> Optional[Tuple[str, List[str]]]:
    """Get pronunciation for a word from database"""
    conn = get_db()
    cur = conn.cursor()
    
    lookup = term.upper().strip()
    cur.execute("SELECT word, pron FROM words WHERE word = ? LIMIT 1", (lookup,))
    row = cur.fetchone()
    
    conn.close()
    
    if row:
        word, pron = row
        phonemes = pron.split()
        return (word, phonemes)
    
    return None

def extract_rhyme_keys(phonemes: List[str]) -> Tuple[str, str, str]:
    """Extract rhyme keys K1, K2, K3"""
    last_stress_idx = -1
    for i in range(len(phonemes) - 1, -1, -1):
        if phonemes[i][-1] in '12':
            last_stress_idx = i
            break
    
    if last_stress_idx == -1:
        return ("", "", "")
    
    stressed_vowel = phonemes[last_stress_idx]
    tail = phonemes[last_stress_idx + 1:] if last_stress_idx < len(phonemes) - 1 else []
    
    k1 = strip_stress(stressed_vowel)
    k2 = strip_stress(stressed_vowel) + ("|" + " ".join(tail) if tail else "")
    k3 = stressed_vowel + ("|" + " ".join(tail) if tail else "")
    
    return (k1, k2, k3)

def score_rhyme(target_phonemes: List[str], candidate_phonemes: List[str],
                target_k1: str, target_k2: str, target_k3: str,
                candidate_k1: str, candidate_k2: str, candidate_k3: str,
                enable_alliteration: bool = True) -> Tuple[float, Dict[str, Any]]:
    """
    Score rhyme quality with comprehensive metadata.
    Returns (score, metadata) with all analysis details.
    """
    base_score = 0.0
    metadata = {
        'has_alliteration': False,
        'matching_syllables': 0,
        'onset_match': False,
        'coda_similarity': 0.0,
        'meter': '',
        'subcategory': 'fallback'
    }
    
    # Extract meter
    stress_pattern = extract_stress_pattern(candidate_phonemes)
    metadata['meter'] = get_meter_type(stress_pattern)
    
    # Perfect rhymes
    if candidate_k3 == target_k3 and target_k3:
        base_score = 1.00
        metadata['subcategory'] = 'k3_perfect'
    elif candidate_k2 == target_k2 and target_k2:
        base_score = 0.85
        metadata['subcategory'] = 'k2_perfect'
    else:
        # Calculate similarities
        phon_sim = calculate_phonetic_similarity(target_phonemes, candidate_phonemes)
        coda_sim = calculate_coda_similarity(target_phonemes, candidate_phonemes)
        metadata['coda_similarity'] = coda_sim
        
        # K1 match (assonance) + similarity
        if candidate_k1 == target_k1 and target_k1:
            if phon_sim >= 0.70 or coda_sim >= 0.70:
                base_score = 0.60 + min(0.14, (phon_sim - 0.70) * 0.14 / 0.30 + coda_sim * 0.1)
                metadata['subcategory'] = 'near_perfect'
            elif phon_sim >= 0.50:
                base_score = 0.35 + (phon_sim - 0.50) * 0.24 / 0.20
                metadata['subcategory'] = 'assonance'
            else:
                base_score = 0.20 + phon_sim * 0.15
                metadata['subcategory'] = 'assonance'
        
        # Consonance
        elif phon_sim >= 0.40 or coda_sim >= 0.60:
            base_score = 0.30
            metadata['subcategory'] = 'consonance'
        
        # Stress pattern match
        else:
            target_stress = extract_stress_pattern(target_phonemes)
            candidate_stress = extract_stress_pattern(candidate_phonemes)
            if target_stress == candidate_stress and target_stress:
                base_score = 0.15
                metadata['subcategory'] = 'stress_match'
    
    # Alliteration bonus
    if enable_alliteration:
        target_onset = extract_onset(target_phonemes)
        candidate_onset = extract_onset(candidate_phonemes)
        
        if target_onset and candidate_onset:
            if target_onset == candidate_onset:
                metadata['has_alliteration'] = True
                metadata['onset_match'] = True
                base_score += cfg.alliteration_bonus
            elif target_onset[0] == candidate_onset[0]:
                metadata['has_alliteration'] = True
                base_score += cfg.alliteration_bonus * 0.5
    
    # Multi-syllable bonus
    matching_syls = count_matching_syllables(target_phonemes, candidate_phonemes)
    metadata['matching_syllables'] = matching_syls
    if matching_syls >= 2:
        base_score += cfg.multisyl_bonus
    
    return (min(1.0, base_score), metadata)

def search_rhymes(term: str, syl_filter: str = "Any", stress_filter: str = "Any",
                  use_datamuse: bool = True, multisyl_only: bool = False,
                  enable_alliteration: bool = True) -> Dict[str, Any]:
    """
    Complete search with all features preserved.
    Returns comprehensive categorized results with all metadata.
    """
    result = {
        "perfect": {"popular": [], "technical": []},
        "slant": {
            "near_perfect": {"popular": [], "technical": []},
            "assonance": {"popular": [], "technical": []},
            "fallback": []
        },
        "colloquial": [],
        "rap": [],
        "query_info": {},
        "keys": {}
    }
    
    # Get target word
    target_data = get_word_pronunciation(term)
    if not target_data:
        return result
    
    target_word, target_phonemes = target_data
    target_k1, target_k2, target_k3 = extract_rhyme_keys(target_phonemes)
    
    if not target_k1:
        return result
    
    # Query metadata
    target_stress = extract_stress_pattern(target_phonemes)
    target_meter = get_meter_type(target_stress)
    
    result["query_info"] = {
        "word": term,
        "pron": " ".join(target_phonemes),
        "stress": target_stress,
        "meter": target_meter,
        "syls": sum(1 for p in target_phonemes if is_vowel(p))
    }
    
    result["keys"] = {
        "k1": target_k1,
        "k2": target_k2,
        "k3": target_k3
    }
    
    # Get Datamuse data
    datamuse_data = {'single': [], 'multi': [], 'all_words': set()}
    if use_datamuse:
        datamuse_data = query_datamuse(term)
    
    # Search database
    conn = get_db()
    cur = conn.cursor()
    
    # Build filters
    conditions = ["word != ?"]
    params = [target_word]
    
    if syl_filter != "Any":
        if syl_filter == "5+":
            conditions.append("syls >= 5")
        else:
            conditions.append("syls = ?")
            params.append(int(syl_filter))
    
    if stress_filter != "Any":
        conditions.append("stress = ?")
        params.append(stress_filter)
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT word, pron, k1, k2, k3, zipf, syls, stress
        FROM words
        WHERE {where_clause}
    """
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    # Process results
    cmu_results = []
    for row in rows:
        word, pron, k1, k2, k3, zipf, syls, stress = row
        phonemes = pron.split()
        
        score, metadata = score_rhyme(
            target_phonemes, phonemes,
            target_k1, target_k2, target_k3,
            k1, k2, k3,
            enable_alliteration
        )
        
        if score < 0.15:
            continue
        
        if multisyl_only and metadata['matching_syllables'] < 2:
            continue
        
        # Build visual indicators
        is_popular = word.lower() in datamuse_data['all_words']
        indicators = []
        
        if metadata['subcategory'] in EMOJI:
            indicators.append(EMOJI[metadata['subcategory']])
        if not is_popular:
            indicators.append(EMOJI['technical'])
        if metadata['has_alliteration']:
            indicators.append(EMOJI['alliteration'])
        if metadata['matching_syllables'] >= 2:
            indicators.append(EMOJI['multisyl'])
        
        cmu_results.append({
            'word': word.lower(),
            'score': score,
            'zipf': zipf,
            'syls': syls,
            'stress': stress,
            'pron': pron,
            'is_popular': is_popular,
            'has_alliteration': metadata['has_alliteration'],
            'matching_syllables': metadata['matching_syllables'],
            'meter': metadata['meter'],
            'subcategory': metadata['subcategory'],
            'coda_similarity': metadata['coda_similarity'],
            'indicators': ' '.join(indicators)
        })
    
    # Sort by score and zipf
    cmu_results.sort(key=lambda x: (-x['score'], x['zipf']))
    
    # Categorize
    for item in cmu_results:
        score = item['score']
        zipf = item['zipf']
        
        if score < 0.85 and zipf > cfg.zipf_max_slant:
            continue
        
        # Determine category
        if score >= 0.85:
            category = "popular" if item['is_popular'] else "technical"
            if len(result["perfect"][category]) < cfg.max_items:
                result["perfect"][category].append(item)
        
        elif score >= 0.60:
            category = "popular" if item['is_popular'] else "technical"
            if len(result["slant"]["near_perfect"][category]) < cfg.max_items:
                result["slant"]["near_perfect"][category].append(item)
        
        elif score >= 0.35:
            category = "popular" if item['is_popular'] else "technical"
            if len(result["slant"]["assonance"][category]) < cfg.max_items:
                result["slant"]["assonance"][category].append(item)
        
        else:
            if len(result["slant"]["fallback"]) < cfg.max_items:
                result["slant"]["fallback"].append(item)
    
    # Add colloquial phrases
    for phrase_item in datamuse_data['multi']:
        if len(result["colloquial"]) >= cfg.max_items:
            break
        result["colloquial"].append({
            'word': phrase_item['word'],
            'score': 0.95,
            'zipf': 5.0,
            'syls': phrase_item['word'].count(' ') + 1,
            'stress': 'phrase',
            'pron': '',
            'is_popular': True,
            'has_alliteration': False,
            'matching_syllables': 0,
            'indicators': f"{EMOJI['multiword']} {EMOJI['datamuse']}"
        })
    
    return result

def get_result_counts(results: Dict[str, Any]) -> Dict[str, int]:
    """Count results in each category"""
    counts = {
        'perfect_popular': len(results['perfect']['popular']),
        'perfect_technical': len(results['perfect']['technical']),
        'near_perfect_popular': len(results['slant']['near_perfect']['popular']),
        'near_perfect_technical': len(results['slant']['near_perfect']['technical']),
        'assonance_popular': len(results['slant']['assonance']['popular']),
        'assonance_technical': len(results['slant']['assonance']['technical']),
        'fallback': len(results['slant']['fallback']),
        'colloquial': len(results['colloquial']),
        'rap': len(results['rap'])
    }
    
    counts['total_slant'] = (
        counts['near_perfect_popular'] + counts['near_perfect_technical'] +
        counts['assonance_popular'] + counts['assonance_technical']
    )
    
    return counts

def organize_by_syllables(items: List[Dict]) -> Dict[int, List[Dict]]:
    """Organize results by syllable count"""
    by_syl = defaultdict(list)
    for item in items:
        by_syl[item['syls']].append(item)
    return dict(sorted(by_syl.items()))