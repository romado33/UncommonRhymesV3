"""
Targeted test to see what's filtering out the perfect rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import get_phonetic_keys, query_perfect_rhymes, cfg
import sqlite3

def test_perfect_rhyme_filtering():
    """Test what's filtering out perfect rhymes"""
    
    config = cfg
    target_word = "table"
    
    print(f"Testing perfect rhyme filtering for '{target_word}'")
    print("="*60)
    
    # Get K3 key and query directly
    keys = get_phonetic_keys(target_word, config)
    k1, k2, k3 = keys
    
    # Get target syllable count
    conn = sqlite3.connect(config.db_path)
    cur = conn.cursor()
    cur.execute("SELECT syls FROM words WHERE word = ?", (target_word.lower(),))
    result = cur.fetchone()
    target_syls = result[0] if result else 0
    conn.close()
    
    print(f"Target: {target_word}")
    print(f"K3 key: {k3}")
    print(f"Target syllables: {target_syls}")
    print("="*60)
    
    # Query CMU database directly
    cmu_perfect = query_perfect_rhymes(k3, target_word, config)
    print(f"Direct CMU query found: {len(cmu_perfect)} perfect rhymes")
    
    # Test each filter step by step
    print("\nTesting filters step by step:")
    
    filtered_count = 0
    for word, zipf, word_k1, word_k2, word_k3 in cmu_perfect:
        print(f"\nTesting: {word} (zipf: {zipf:.1f})")
        
        # Check stop words
        if word.lower() in config.ultra_common_stop_words:
            print(f"  X Filtered out: stop word")
            filtered_count += 1
            continue
        
        # Get word data
        conn = sqlite3.connect(config.db_path)
        cur = conn.cursor()
        cur.execute("SELECT syls, stress, pron FROM words WHERE word = ?", (word.lower(),))
        word_data = cur.fetchone()
        conn.close()
        
        if not word_data:
            print(f"  X Filtered out: no word data")
            filtered_count += 1
            continue
        
        syls, stress, pron = word_data
        print(f"  Syllables: {syls}")
        
        # Check syllable filtering (should be removed for perfect rhymes)
        if target_syls > 0 and syls < target_syls:
            print(f"  X Filtered out: syllable filtering (syls < target)")
            filtered_count += 1
            continue
        
        # Check multi-syllable filter (default is False)
        multisyl_only = False  # Default value
        if multisyl_only and syls < 2:
            print(f"  X Filtered out: multi-syllable filter")
            filtered_count += 1
            continue
        
        print(f"  [OK] Passed all filters")
    
    print(f"\nSummary:")
    print(f"  Total perfect rhymes: {len(cmu_perfect)}")
    print(f"  Filtered out: {filtered_count}")
    print(f"  Should remain: {len(cmu_perfect) - filtered_count}")

if __name__ == "__main__":
    test_perfect_rhyme_filtering()
