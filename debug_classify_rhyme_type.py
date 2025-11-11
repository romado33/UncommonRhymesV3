"""
Debug script to test classify_rhyme_type function directly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import get_pronunciation_from_db, get_zipf_frequency, classify_rhyme_type, calculate_wrs
from rhyme_core.phonetics import parse_pron, k_keys
from rhyme_core.engine import cfg

def debug_classify_rhyme_type():
    """Debug the classify_rhyme_type function"""
    
    target_word = "table"
    
    print(f"Debugging classify_rhyme_type for '{target_word}'")
    print("="*60)
    
    # Get target word data
    target_pron = get_pronunciation_from_db(target_word)
    if not target_pron:
        print(f"ERROR: No pronunciation found for '{target_word}'")
        return
    
    target_phones = parse_pron(target_pron)
    target_k1, target_k2, target_k3 = k_keys(target_phones)
    target_zipf = get_zipf_frequency(target_word) or 5.0
    
    print(f"Target: {target_word}")
    print(f"  Pronunciation: {target_pron}")
    print(f"  K3 key: {target_k3}")
    print(f"  Zipf: {target_zipf}")
    
    # Test with some known perfect rhymes
    test_words = [
        ("stable", 30.7, 13052.0),  # Should be popular
        ("cable", 14.4, 5070.0),    # Should be popular  
        ("label", 13.9, 14054.0),   # Should be popular
        ("enable", 19.7, 35038.0),  # Should be popular
        ("fable", 2.0, 22040.0),    # Should be popular (score > 30)
        ("disable", 1.1, 8038.0),   # Should be popular (score > 30)
        ("unable", 34.0, 2031.0),   # Should be popular (freq > 2.0)
    ]
    
    print(f"\nTesting classify_rhyme_type:")
    print(f"{'Word':<12} {'Freq':<8} {'Score':<8} {'Rhyme':<12} {'Category':<10} {'K3 Match'}")
    print("-" * 70)
    
    for word, freq, score in test_words:
        word_pron = get_pronunciation_from_db(word)
        if not word_pron:
            print(f"{word:<12} {freq:<8.1f} {score:<8.1f} {'NO PRON':<12} {'N/A':<10} {'N/A'}")
            continue
        
        word_phones = parse_pron(word_pron)
        word_k1, word_k2, word_k3 = k_keys(word_phones)
        word_zipf = get_zipf_frequency(word) or 5.0
        
        # Calculate WRS score
        wrs_score = calculate_wrs(target_phones, word_phones, target_zipf, word_zipf)
        
        # Classify rhyme type
        rhyme_type, category = classify_rhyme_type(
            target_phones, word_phones, wrs_score,
            target_k1, target_k2, target_k3,
            word_k1, word_k2, word_k3,
            freq, score
        )
        
        k3_match = target_k3 == word_k3
        
        print(f"{word:<12} {freq:<8.1f} {score:<8.1f} {rhyme_type:<12} {category:<10} {k3_match}")

if __name__ == "__main__":
    debug_classify_rhyme_type()




