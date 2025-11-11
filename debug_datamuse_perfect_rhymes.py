"""
Debug script to examine raw Datamuse data for perfect rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import fetch_datamuse_comprehensive, get_pronunciation_from_db
from rhyme_core.phonetics import parse_pron, k_keys
import json

def debug_datamuse_perfect_rhymes():
    """Debug the raw Datamuse data for perfect rhymes"""
    
    target_word = "table"
    
    print(f"Debugging Datamuse perfect rhymes for '{target_word}'")
    print("="*60)
    
    # Get target word's K3 key
    target_pron = get_pronunciation_from_db(target_word)
    if not target_pron:
        print(f"ERROR: No pronunciation found for '{target_word}'")
        return
    
    print(f"Target pronunciation: {target_pron}")
    
    target_phones = parse_pron(target_pron)
    if not target_phones:
        print(f"ERROR: No phones parsed for '{target_word}'")
        return
    
    k1, k2, k3 = k_keys(target_phones)
    print(f"Target K3 key: {k3}")
    
    # Fetch Datamuse data
    print("\nFetching Datamuse data...")
    datamuse_results = fetch_datamuse_comprehensive(target_word)
    
    print(f"Datamuse results keys: {list(datamuse_results.keys())}")
    
    # Check perfect rhymes (already processed by fetch_datamuse_comprehensive)
    if 'perfect' in datamuse_results:
        perfect_rhymes = datamuse_results['perfect']
        print(f"\nperfect rhymes: {len(perfect_rhymes)} items")
        
        # Show first 10 with their freq/score
        for i, item in enumerate(perfect_rhymes[:10]):
            word = item.get('word', '')
            freq = item.get('freq', 0)
            score = item.get('score', 0)
            
            # Check if it's actually a perfect rhyme
            word_pron = get_pronunciation_from_db(word)
            if word_pron:
                word_phones = parse_pron(word_pron)
                if word_phones:
                    word_k1, word_k2, word_k3 = k_keys(word_phones)
                    is_perfect = word_k3 == k3
                    print(f"  {i+1:2d}. {word:12s} freq={freq:6.1f} score={score:6.1f} perfect={is_perfect} k3={word_k3}")
                else:
                    print(f"  {i+1:2d}. {word:12s} freq={freq:6.1f} score={score:6.1f} perfect=? (no phones)")
            else:
                print(f"  {i+1:2d}. {word:12s} freq={freq:6.1f} score={score:6.1f} perfect=? (no pron)")
        
        # Check categorization thresholds
        print(f"\nCategorization thresholds:")
        print(f"  Popular: freq > 2.0 OR score > 30")
        print(f"  Technical: freq <= 2.0 AND score <= 30")
        
        # Count how many would be popular vs technical
        popular_count = 0
        technical_count = 0
        perfect_count = 0
        
        for item in perfect_rhymes:
            freq = item.get('freq', 0)
            score = item.get('score', 0)
            word = item.get('word', '')
            
            # Check if it's actually a perfect rhyme
            word_pron = get_pronunciation_from_db(word)
            if word_pron:
                word_phones = parse_pron(word_pron)
                if word_phones:
                    word_k1, word_k2, word_k3 = k_keys(word_phones)
                    if word_k3 == k3:
                        perfect_count += 1
                        if freq > 2.0 or score > 30:
                            popular_count += 1
                        else:
                            technical_count += 1
        
        print(f"\nPerfect rhyme categorization:")
        print(f"  Total perfect rhymes: {perfect_count}")
        print(f"  Would be popular: {popular_count}")
        print(f"  Would be technical: {technical_count}")
        
        # Show some examples of each category
        print(f"\nPopular perfect rhymes (freq > 2.0 or score > 30):")
        popular_examples = []
        for item in perfect_rhymes:
            freq = item.get('freq', 0)
            score = item.get('score', 0)
            word = item.get('word', '')
            
            if freq > 2.0 or score > 30:
                word_pron = get_pronunciation_from_db(word)
                if word_pron:
                    word_phones = parse_pron(word_pron)
                    if word_phones:
                        word_k1, word_k2, word_k3 = k_keys(word_phones)
                        if word_k3 == k3:
                            popular_examples.append((word, freq, score))
        
        for word, freq, score in popular_examples[:10]:
            print(f"  {word:12s} freq={freq:6.1f} score={score:6.1f}")
    
    else:
        print("No perfect rhymes found")

if __name__ == "__main__":
    debug_datamuse_perfect_rhymes()
