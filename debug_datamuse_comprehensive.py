"""
Debug script to test fetch_datamuse_comprehensive directly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import fetch_datamuse_comprehensive, cfg
import traceback

def debug_datamuse_comprehensive():
    """Debug fetch_datamuse_comprehensive directly"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging fetch_datamuse_comprehensive for '{target_word}'")
    print("="*60)
    
    try:
        datamuse_results = fetch_datamuse_comprehensive(
            target_word,
            max_perfect=1000,
            max_near=1000,
            max_approx=1000,
            max_sounds_like=1000,
            max_homophones=500,
            max_consonants=500,
            max_synonyms=500,
            max_triggers=500,
            timeout=config.datamuse_timeout,
            config=config
        )
        
        print("Datamuse call completed successfully")
        print(f"Results keys: {list(datamuse_results.keys())}")
        
        for key, results in datamuse_results.items():
            print(f"  {key}: {len(results)} results")
            if results and key == 'perfect':
                print(f"    First few: {[r['word'] for r in results[:3]]}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_datamuse_comprehensive()




