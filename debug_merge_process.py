"""
Debug script to trace the merge process and see what's happening to CMU results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, get_phonetic_keys, query_perfect_rhymes, merge_cmu_and_datamuse_results, cfg
import sqlite3

def debug_merge_process():
    """Debug what's happening in the merge process"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging merge process for '{target_word}'")
    print("="*60)
    
    # Step 1: Get CMU results directly
    keys = get_phonetic_keys(target_word, config)
    k1, k2, k3 = keys
    
    cmu_perfect = query_perfect_rhymes(k3, target_word, config)
    print(f"Direct CMU query: {len(cmu_perfect)} perfect rhymes")
    
    # Step 2: Simulate the CMU processing that happens in search_rhymes
    print("\nStep 2: Simulating CMU processing")
    
    # Get target syllable count
    conn = sqlite3.connect(config.db_path)
    cur = conn.cursor()
    cur.execute("SELECT syls FROM words WHERE word = ?", (target_word.lower(),))
    result = cur.fetchone()
    target_syls = result[0] if result else 0
    conn.close()
    
    # Process CMU results like search_rhymes does
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
    for word, zipf, word_k1, word_k2, word_k3 in cmu_perfect:
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
        
        # NOTE: Syllable filtering removed for perfect rhymes
        # Perfect rhymes are exact phonetic matches and should not be filtered by syllable count
        # The user's requirement was specifically about slant rhymes, not perfect rhymes
        
        # Create match entry
        match_entry = {
            'word': word,
            'syllables': syls,
            'stress_pattern': stress,
            'pronunciation': pron,
            'metrical_pattern': '',  # Will be calculated later
            'score': 90 + (3 if zipf >= 3.0 else 0),
            'source': 'cmu',
            'datamuse_verified': False,
            'has_alliteration': word[0].lower() == target_word[0].lower(),
            'matching_syllables': 0
        }
        
        if zipf >= 1.5:  # Further lowered threshold for perfect rhymes
            cmu_results['perfect']['popular'].append(match_entry)
        else:
            cmu_results['perfect']['technical'].append(match_entry)
        
        processed_count += 1
    
    print(f"CMU processing result:")
    print(f"  Popular: {len(cmu_results['perfect']['popular'])}")
    print(f"  Technical: {len(cmu_results['perfect']['technical'])}")
    print(f"  Total processed: {processed_count}")
    
    # Step 3: Check what happens in the merge process
    print("\nStep 3: Checking merge process")
    
    # Create empty Datamuse results for now
    datamuse_results = {
        'perfect': [],
        'near': [],
        'homophones': [],
        'consonants': [],
        'synonyms': [],
        'triggers': []
    }
    
    # Run the merge process
    merged = merge_cmu_and_datamuse_results(
        cmu_results, datamuse_results, target_word, target_syls,
        max_per_category=50, enable_alliteration=True, config=config
    )
    
    print(f"Merge result:")
    print(f"  Popular: {len(merged['perfect']['popular'])}")
    print(f"  Technical: {len(merged['perfect']['technical'])}")
    
    # Check if any words were lost
    cmu_words = set()
    cmu_words.update(item['word'] for item in cmu_results['perfect']['popular'])
    cmu_words.update(item['word'] for item in cmu_results['perfect']['technical'])
    
    merged_words = set()
    merged_words.update(item['word'] for item in merged['perfect']['popular'])
    merged_words.update(item['word'] for item in merged['perfect']['technical'])
    
    lost_words = cmu_words - merged_words
    if lost_words:
        print(f"  Lost words: {list(lost_words)[:10]}")
    else:
        print(f"  No words lost in merge")

if __name__ == "__main__":
    debug_merge_process()
