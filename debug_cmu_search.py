"""
Debug script to investigate why CMU search is missing perfect rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import get_phonetic_keys, query_perfect_rhymes, search_rhymes
from rhyme_core.config import PrecisionConfig

def debug_cmu_search_issue():
    """Debug why CMU search is missing perfect rhymes"""
    
    config = PrecisionConfig()
    target_word = "table"
    
    print(f"Debugging CMU search for '{target_word}'")
    print("="*60)
    
    # Step 1: Get K3 key and query directly
    keys = get_phonetic_keys(target_word, config)
    if not keys:
        print("ERROR: Could not get phonetic keys")
        return
    
    k1, k2, k3 = keys
    print(f"K3 key: {k3}")
    
    # Step 2: Query CMU database directly
    cmu_perfect = query_perfect_rhymes(k3, target_word, config)
    print(f"Direct CMU query found: {len(cmu_perfect)} perfect rhymes")
    
    # Step 3: Check what the search_rhymes function actually finds
    print("\nStep 3: What search_rhymes actually finds")
    
    # Let's look at the CMU search function directly
    from rhyme_core.engine import search_cmu_rhymes
    
    cmu_results = search_cmu_rhymes(target_word, config)
    cmu_perfect_found = cmu_results.get('perfect', {})
    cmu_popular = cmu_perfect_found.get('popular', [])
    cmu_technical = cmu_perfect_found.get('technical', [])
    
    print(f"search_cmu_rhymes found:")
    print(f"  Popular: {len(cmu_popular)}")
    print(f"  Technical: {len(cmu_technical)}")
    
    if cmu_popular:
        print(f"  Popular words: {[item['word'] for item in cmu_popular[:5]]}")
    if cmu_technical:
        print(f"  Technical words: {[item['word'] for item in cmu_technical[:5]]}")
    
    # Step 4: Compare with direct query
    print(f"\nStep 4: Comparison with direct query")
    
    direct_words = set(word for word, _, _, _, _ in cmu_perfect)
    search_words = set()
    search_words.update(item['word'] for item in cmu_popular)
    search_words.update(item['word'] for item in cmu_technical)
    
    missing_from_search = direct_words - search_words
    extra_in_search = search_words - direct_words
    
    print(f"Missing from search: {len(missing_from_search)}")
    if missing_from_search:
        print(f"  Missing words: {list(missing_from_search)[:10]}")
    
    print(f"Extra in search: {len(extra_in_search)}")
    if extra_in_search:
        print(f"  Extra words: {list(extra_in_search)[:10]}")
    
    # Step 5: Check if it's a filtering issue
    print(f"\nStep 5: Checking filtering")
    
    # Check if any of the missing words are in stop words
    missing_stop_words = []
    for word in missing_from_search:
        if word.lower() in config.ultra_common_stop_words:
            missing_stop_words.append(word)
    
    if missing_stop_words:
        print(f"Missing words that are stop words: {missing_stop_words}")
    
    # Step 6: Check if it's a syllable filtering issue
    print(f"\nStep 6: Checking syllable filtering")
    
    target_syls = None
    for word, _, _, _, _ in cmu_perfect:
        if word.lower() == target_word.lower():
            # This should be the target word itself
            continue
        
        # Check if syllable filtering is removing words
        # Let's see what the syllable count is for the target
        if target_syls is None:
            # Get target syllable count
            import sqlite3
            conn = sqlite3.connect(config.db_path)
            cur = conn.cursor()
            cur.execute("SELECT syls FROM words WHERE word = ?", (target_word.lower(),))
            result = cur.fetchone()
            if result:
                target_syls = result[0]
            conn.close()
            print(f"Target syllable count: {target_syls}")
        
        # Check each missing word's syllable count
        if word in missing_from_search:
            conn = sqlite3.connect(config.db_path)
            cur = conn.cursor()
            cur.execute("SELECT syls FROM words WHERE word = ?", (word.lower(),))
            result = cur.fetchone()
            if result:
                word_syls = result[0]
                if word_syls and target_syls and word_syls < target_syls:
                    print(f"  {word}: {word_syls} syllables (filtered out - fewer than target {target_syls})")
            conn.close()

if __name__ == "__main__":
    debug_cmu_search_issue()

