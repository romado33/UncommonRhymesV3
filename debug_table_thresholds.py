"""
Debug script to investigate thresholds for "table" perfect rhymes
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.phonetics import parse_pron, k_keys
from rhyme_core.engine import get_pronunciation_from_db
from rhyme_core.config import PrecisionConfig

def debug_table_thresholds():
    """Debug thresholds for table perfect rhymes"""
    
    config = PrecisionConfig()
    target_word = "table"
    
    # Get target word pronunciation and K3 key
    target_pron = get_pronunciation_from_db(target_word, config)
    target_phones = parse_pron(target_pron)
    k1, k2, k3 = k_keys(target_phones)
    
    print(f"Target: {target_word}")
    print(f"K3 key: {k3}")
    print("="*60)
    
    # Query CMU database for K3 matches
    conn = sqlite3.connect(config.db_path)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT word, zipf, k1, k2, k3, syls, stress, pron
        FROM words 
        WHERE k3 = ? AND word != ?
        ORDER BY zipf DESC
    """, (k3, target_word.lower()))
    
    cmu_results = cur.fetchall()
    conn.close()
    
    print(f"CMU Perfect Rhymes (K3 matches): {len(cmu_results)}")
    print("="*60)
    print(f"{'Word':<15} {'Zipf':<6} {'Popular?':<10} {'Threshold':<10}")
    print("="*60)
    
    popular_count = 0
    technical_count = 0
    
    for word, zipf, word_k1, word_k2, word_k3, syls, stress, pron in cmu_results:
        is_popular = zipf >= 1.5
        category = "Popular" if is_popular else "Technical"
        threshold_status = f"zipf >= 1.5" if is_popular else f"zipf < 1.5"
        
        print(f"{word:<15} {zipf:<6.1f} {category:<10} {threshold_status}")
        
        if is_popular:
            popular_count += 1
        else:
            technical_count += 1
    
    print("="*60)
    print(f"Summary:")
    print(f"- Popular perfect rhymes (zipf >= 1.5): {popular_count}")
    print(f"- Technical perfect rhymes (zipf < 1.5): {technical_count}")
    print(f"- Total perfect rhymes: {len(cmu_results)}")
    
    # Check what the actual Zipf range is
    if cmu_results:
        max_zipf = max(r[1] for r in cmu_results)
        min_zipf = min(r[1] for r in cmu_results)
        print(f"- Zipf range: {min_zipf:.1f} to {max_zipf:.1f}")
        
        # Show how many would be popular with different thresholds
        thresholds = [1.0, 1.5, 2.0, 2.5, 3.0]
        print(f"\nThreshold Analysis:")
        for threshold in thresholds:
            count = sum(1 for r in cmu_results if r[1] >= threshold)
            print(f"- zipf >= {threshold}: {count} popular rhymes")

if __name__ == "__main__":
    debug_table_thresholds()
