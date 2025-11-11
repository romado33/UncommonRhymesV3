"""
Quick fix: Disable uncommon filter for perfect rhymes to show all of them
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_without_uncommon_filter():
    """Test search_rhymes without uncommon filter to see all perfect rhymes"""
    
    target_word = "table"
    
    print(f"Testing '{target_word}' without uncommon filter")
    print("="*60)
    
    # Temporarily disable uncommon filter by modifying the config
    import rhyme_core.engine
    
    # Get the original config
    original_config = rhyme_core.engine.cfg
    
    # Create a modified config that disables uncommon filtering
    from rhyme_core.uncommon_filter import UncommonConfig
    from rhyme_core.engine import PrecisionConfig
    
    # Create new config with uncommon filter disabled
    new_config = PrecisionConfig(
        db_path=original_config.db_path,
        use_datamuse=original_config.use_datamuse,
        use_uncommon_filter=False,  # Disable uncommon filter
        uncommon_config=UncommonConfig(
            min_perfect_rhymes=1000,  # Show all perfect rhymes
            min_total_results=50,     # Show more total results
            min_per_category=10       # Show more per category
        )
    )
    
    # Temporarily replace the config
    rhyme_core.engine.cfg = new_config
    
    try:
        # Run the search
        results = search_rhymes(target_word, use_datamuse=True)
        
        print(f"Results without uncommon filter:")
        print(f"  Perfect popular: {len(results.get('perfect', {}).get('popular', []))}")
        print(f"  Perfect technical: {len(results.get('perfect', {}).get('technical', []))}")
        print(f"  Total perfect: {len(results.get('perfect', {}).get('popular', [])) + len(results.get('perfect', {}).get('technical', []))}")
        
        # Show some examples
        perfect_popular = results.get('perfect', {}).get('popular', [])
        perfect_technical = results.get('perfect', {}).get('technical', [])
        
        if perfect_popular:
            print(f"  Popular perfect examples: {[w['word'] for w in perfect_popular[:10]]}")
        if perfect_technical:
            print(f"  Technical perfect examples: {[w['word'] for w in perfect_technical[:10]]}")
        
        # Check metadata
        if 'metadata' in results:
            print(f"  Metadata keys: {list(results['metadata'].keys())}")
            if 'datamuse_calls' in results['metadata']:
                print(f"  Datamuse calls: {results['metadata']['datamuse_calls']}")
        
    finally:
        # Restore the original config
        rhyme_core.engine.cfg = original_config

if __name__ == "__main__":
    test_without_uncommon_filter()




