"""
Debug script to investigate K1 assonance matching for "table"
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.phonetics import parse_pron, k_keys
from rhyme_core.engine import get_pronunciation_from_db
from rhyme_core.config import PrecisionConfig

def debug_assonance_matching():
    """Debug K1 assonance matching for table"""
    
    config = PrecisionConfig()
    target_word = "table"
    
    # Get target word pronunciation and K keys
    target_pron = get_pronunciation_from_db(target_word, config)
    target_phones = parse_pron(target_pron)
    k1, k2, k3 = k_keys(target_phones)
    
    print(f"Target: {target_word}")
    print(f"K1 key: {k1}")
    print(f"K2 key: {k2}")
    print(f"K3 key: {k3}")
    print("="*60)
    
    # Query CMU database for K1 matches (assonance)
    conn = sqlite3.connect(config.db_path)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT word, zipf, k1, k2, k3, syls, stress, pron
        FROM words 
        WHERE k1 = ? AND word != ? AND k2 != ?
        ORDER BY zipf DESC
        LIMIT 50
    """, (k1, target_word.lower(), k2))  # K1 match but NOT K2 match (so not perfect)
    
    assonance_results = cur.fetchall()
    conn.close()
    
    print(f"CMU Assonance Rhymes (K1 matches, not K2): {len(assonance_results)}")
    print("="*60)
    print(f"{'Word':<15} {'Zipf':<6} {'K1':<8} {'K2':<15} {'K3':<15}")
    print("="*60)
    
    for word, zipf, word_k1, word_k2, word_k3, syls, stress, pron in assonance_results:
        print(f"{word:<15} {zipf:<6.1f} {word_k1:<8} {word_k2:<15} {word_k3:<15}")
    
    print("="*60)
    
    # Also check what happens if we look for K2 matches that are NOT K3
    conn = sqlite3.connect(config.db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT word, zipf, k1, k2, k3, syls, stress, pron
        FROM words 
        WHERE k2 = ? AND word != ? AND k3 != ?
        ORDER BY zipf DESC
        LIMIT 20
    """, (k2, target_word.lower(), k3))  # K2 match but NOT K3 match
    
    near_perfect_results = cur.fetchall()
    conn.close()
    
    print(f"\nCMU Near-Perfect Rhymes (K2 matches, not K3): {len(near_perfect_results)}")
    print("="*60)
    print(f"{'Word':<15} {'Zipf':<6} {'K1':<8} {'K2':<15} {'K3':<15}")
    print("="*60)
    
    for word, zipf, word_k1, word_k2, word_k3, syls, stress, pron in near_perfect_results:
        print(f"{word:<15} {zipf:<6.1f} {word_k1:<8} {word_k2:<15} {word_k3:<15}")
    
    print("="*60)
    print(f"Summary:")
    print(f"- Perfect rhymes (K3): 31 (from previous analysis)")
    print(f"- Near-perfect rhymes (K2, not K3): {len(near_perfect_results)}")
    print(f"- Assonance rhymes (K1, not K2): {len(assonance_results)}")

if __name__ == "__main__":
    debug_assonance_matching()
