"""
Debug script to add logging to search_rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import get_phonetic_keys, query_perfect_rhymes, cfg
import sqlite3

def debug_cmu_search_directly():
    """Debug CMU search directly"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging CMU search directly for '{target_word}'")
    print("="*60)
    
    # Step 1: Get phonetic keys
    keys = get_phonetic_keys(target_word, config)
    if not keys:
        print("X ERROR: No phonetic keys")
        return
    
    k1, k2, k3 = keys
    print(f"K1: {k1}")
    print(f"K2: {k2}")
    print(f"K3: {k3}")
    
    # Step 2: Get target syllable count
    target_syls = 0
    try:
        conn = sqlite3.connect(config.db_path)
        cur = conn.cursor()
        cur.execute("SELECT syls FROM words WHERE word = ?", (target_word.lower(),))
        result = cur.fetchone()
        conn.close()
        if result:
            target_syls = result[0]
    except Exception as e:
        print(f"X ERROR getting target syllables: {e}")
        return
    
    print(f"Target syllables: {target_syls}")
    
    # Step 3: Query perfect rhymes
    try:
        perfect_matches = query_perfect_rhymes(k3, target_word, config)
        print(f"Perfect matches found: {len(perfect_matches)}")
    except Exception as e:
        print(f"X ERROR querying perfect rhymes: {e}")
        return
    
    # Step 4: Process perfect rhymes
    cmu_results = {
        'perfect': {'popular': [], 'technical': []},
        'slant': {
            'near_perfect': {'popular': [], 'technical': []},
            'assonance': {'popular': [], 'technical': []},
            'fallback': []
        },
        'colloquial': []
    }
    
    processed_count = 0
    for word, zipf, word_k1, word_k2, word_k3 in perfect_matches:
        if word.lower() in config.ultra_common_stop_words:
            continue
        
        # Get word data
        conn = sqlite3.connect(config.db_path)
        cur = conn.cursor()
        cur.execute("SELECT syls, stress, pron FROM words WHERE word = ?", (word.lower(),))
        word_data = cur.fetchone()
        conn.close()
        
        if not word_data:
            continue
        
        syls, stress, pron = word_data
        
        # Create match entry
        match_entry = {
            'word': word,
            'syllables': syls,
            'stress_pattern': stress,
            'pronunciation': pron,
            'metrical_pattern': '',
            'score': 90 + (3 if zipf >= 3.0 else 0),
            'source': 'cmu',
            'datamuse_verified': False,
            'has_alliteration': word[0].lower() == target_word[0].lower(),
            'matching_syllables': 0
        }
        
        if zipf >= 1.5:
            cmu_results['perfect']['popular'].append(match_entry)
        else:
            cmu_results['perfect']['technical'].append(match_entry)
        
        processed_count += 1
    
    print(f"\nCMU processing result:")
    print(f"  Popular: {len(cmu_results['perfect']['popular'])}")
    print(f"  Technical: {len(cmu_results['perfect']['technical'])}")
    print(f"  Total processed: {processed_count}")
    
    # Step 5: Add metadata
    cmu_results['metadata'] = {
        'target_word': target_word,
        'search_time': 0.0,
        'phonetic_keys': {'k1': k1, 'k2': k2, 'k3': k3},
        'datamuse_enabled': True,
        'filters_applied': {
            'syllables': 'Any',
            'stress': 'Any',
            'multisyl_only': False,
            'alliteration': True
        }
    }
    
    print(f"\nMetadata added:")
    print(f"  Keys: {list(cmu_results['metadata'].keys())}")
    print(f"  datamuse_enabled: {cmu_results['metadata']['datamuse_enabled']}")

if __name__ == "__main__":
    debug_cmu_search_directly()

