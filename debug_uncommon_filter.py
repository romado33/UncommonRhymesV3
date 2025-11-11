"""
Debug script to test the uncommon filter directly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg
from rhyme_core.uncommon_filter import UncommonFilter, UncommonConfig

def debug_uncommon_filter():
    """Debug the uncommon filter directly"""
    
    target_word = "table"
    
    print(f"Debugging uncommon filter for '{target_word}'")
    print("="*60)
    
    # First, get results without uncommon filter
    print("1. Getting results without uncommon filter...")
    
    # Temporarily disable uncommon filter
    original_use_uncommon_filter = cfg.use_uncommon_filter
    cfg.use_uncommon_filter = False
    
    try:
        results_without_filter = search_rhymes(target_word, use_datamuse=True)
        print(f"   Perfect popular: {len(results_without_filter.get('perfect', {}).get('popular', []))}")
        print(f"   Perfect technical: {len(results_without_filter.get('perfect', {}).get('technical', []))}")
        
        if results_without_filter.get('perfect', {}).get('popular'):
            print(f"   Popular words: {[w['word'] for w in results_without_filter['perfect']['popular'][:5]]}")
    
    finally:
        # Restore original setting
        cfg.use_uncommon_filter = original_use_uncommon_filter
    
    # Now test the uncommon filter directly
    print(f"\n2. Testing uncommon filter directly...")
    
    # Create a test results structure
    test_results = {
        'perfect': {
            'popular': [
                {'word': 'stable', 'category': 'perfect', 'popularity_score': 0.1},
                {'word': 'cable', 'category': 'perfect', 'popularity_score': 0.2},
                {'word': 'label', 'category': 'perfect', 'popularity_score': 0.3},
                {'word': 'enable', 'category': 'perfect', 'popularity_score': 0.4},
                {'word': 'fable', 'category': 'perfect', 'popularity_score': 0.5},
            ],
            'technical': [
                {'word': 'disable', 'category': 'perfect', 'popularity_score': 0.6},
                {'word': 'unable', 'category': 'perfect', 'popularity_score': 0.7},
            ]
        },
        'slant': {
            'near_perfect': {'popular': [], 'technical': []},
            'assonance': {'popular': [], 'technical': []},
        },
        'colloquial': [],
        'metadata': {}
    }
    
    print(f"   Before filter:")
    print(f"     Perfect popular: {len(test_results['perfect']['popular'])}")
    print(f"     Perfect technical: {len(test_results['perfect']['technical'])}")
    
    # Apply uncommon filter
    uncommon_config = UncommonConfig()
    uncommon_filter = UncommonFilter(uncommon_config)
    
    print(f"   Config: min_perfect_rhymes={uncommon_config.min_perfect_rhymes}")
    
    filtered_results = uncommon_filter.apply_uncommon_filter(test_results)
    
    print(f"   After filter:")
    print(f"     Perfect popular: {len(filtered_results.get('perfect', {}).get('popular', []))}")
    print(f"     Perfect technical: {len(filtered_results.get('perfect', {}).get('technical', []))}")
    
    if filtered_results.get('perfect', {}).get('popular'):
        print(f"     Popular words: {[w['word'] for w in filtered_results['perfect']['popular']]}")

if __name__ == "__main__":
    debug_uncommon_filter()




