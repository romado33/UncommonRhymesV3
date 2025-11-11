"""
Debug script to simulate the exact search process for Datamuse perfect rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import fetch_datamuse_comprehensive, get_pronunciation_from_db, get_zipf_frequency, classify_rhyme_type, calculate_wrs
from rhyme_core.phonetics import parse_pron, k_keys
from rhyme_core.engine import cfg
import sqlite3

def debug_search_process():
    """Debug the exact search process for Datamuse perfect rhymes"""
    
    target_word = "table"
    config = cfg
    
    print(f"Debugging search process for '{target_word}'")
    print("="*60)
    
    # Get target word data
    target_pron = get_pronunciation_from_db(target_word, config)
    if not target_pron:
        print(f"ERROR: No pronunciation found for '{target_word}'")
        return
    
    target_phones = parse_pron(target_pron)
    target_k1, target_k2, target_k3 = k_keys(target_phones)
    target_zipf = get_zipf_frequency(target_word, config) or 5.0
    
    print(f"Target: {target_word}")
    print(f"  Pronunciation: {target_pron}")
    print(f"  K3 key: {target_k3}")
    print(f"  Zipf: {target_zipf}")
    
    # Fetch Datamuse data
    print(f"\nFetching Datamuse data...")
    datamuse_results = fetch_datamuse_comprehensive(target_word)
    
    perfect_rhymes = datamuse_results.get('perfect', [])
    print(f"Found {len(perfect_rhymes)} Datamuse perfect rhymes")
    
    # Process each perfect rhyme exactly like the search does
    seen_words = set()
    merged = {
        'perfect': {'popular': [], 'technical': []},
        'slant': {
            'near_perfect': {'popular': [], 'technical': []},
            'terminal_match': {'popular': [], 'technical': []},
            'assonance': {'popular': [], 'technical': []},
            'consonance': {'popular': [], 'technical': []},
            'family_rhymes': {'popular': [], 'technical': []},
            'pararhyme': {'popular': [], 'technical': []},
            'multisyllabic': {'popular': [], 'technical': []},
            'upstream_assonance': {'popular': [], 'technical': []}
        },
        'colloquial': [],
        'metadata': {}
    }
    
    print(f"\nProcessing Datamuse perfect rhymes:")
    print(f"{'Word':<12} {'Freq':<8} {'Score':<8} {'Pron':<15} {'Rhyme':<12} {'Category':<10} {'Added'}")
    print("-" * 80)
    
    for i, dm_result in enumerate(perfect_rhymes[:10]):  # Test first 10
        word = dm_result['word']
        word_lower = word.lower()
        
        if word_lower in seen_words:
            print(f"{word:<12} {'SKIP':<8} {'SKIP':<8} {'DUPLICATE':<15} {'N/A':<12} {'N/A':<10} {'NO'}")
            continue
        
        seen_words.add(word_lower)
        
        # Get pronunciation for this word
        word_pron = get_pronunciation_from_db(word, config)
        if not word_pron:
            print(f"{word:<12} {dm_result['freq']:<8.1f} {dm_result['score']:<8.1f} {'NO PRON':<15} {'N/A':<12} {'N/A':<10} {'NO'}")
            continue
        
        word_phones = parse_pron(word_pron)
        word_k1, word_k2, word_k3 = k_keys(word_phones)
        word_zipf = get_zipf_frequency(word, config) or 5.0
        
        # Calculate WRS score
        wrs_score = calculate_wrs(target_phones, word_phones, target_zipf, word_zipf)
        
        # Classify rhyme type
        rhyme_type, category = classify_rhyme_type(
            target_phones, word_phones, wrs_score,
            target_k1, target_k2, target_k3,
            word_k1, word_k2, word_k3,
            dm_result['freq'], dm_result['score']
        )
        
        # Add to merged results
        if rhyme_type in ['perfect']:
            merged['perfect'][category].append({
                'word': word,
                'rhyme_type': rhyme_type,
                'category': category,
                'freq': dm_result['freq'],
                'score': dm_result['score']
            })
            added = "YES"
        else:
            added = "NO"
        
        print(f"{word:<12} {dm_result['freq']:<8.1f} {dm_result['score']:<8.1f} {word_pron:<15} {rhyme_type:<12} {category:<10} {added}")
    
    print(f"\nFinal merged results:")
    print(f"  Perfect popular: {len(merged['perfect']['popular'])}")
    print(f"  Perfect technical: {len(merged['perfect']['technical'])}")
    
    if merged['perfect']['popular']:
        print(f"  Popular words: {[w['word'] for w in merged['perfect']['popular']]}")

if __name__ == "__main__":
    debug_search_process()




