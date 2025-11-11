"""
Debug script to trace the search_rhymes function execution
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg
import traceback

def debug_search_execution():
    """Debug the search_rhymes function execution"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging search_rhymes execution for '{target_word}'")
    print("="*60)
    
    try:
        # Run search with explicit use_datamuse=True
        print("Running search_rhymes...")
        results = search_rhymes(target_word, use_datamuse=True)
        
        print("Search completed successfully")
        
        # Check metadata
        metadata = results.get('metadata', {})
        print(f"\nMetadata keys: {list(metadata.keys())}")
        
        if 'datamuse_enabled' in metadata:
            print(f"datamuse_enabled: {metadata['datamuse_enabled']}")
        else:
            print("datamuse_enabled: NOT FOUND")
        
        if 'search_time' in metadata:
            print(f"search_time: {metadata['search_time']}")
        else:
            print("search_time: NOT FOUND")
        
        # Check results structure
        print(f"\nResults structure:")
        print(f"  Keys: {list(results.keys())}")
        
        if 'perfect' in results:
            print(f"  Perfect keys: {list(results['perfect'].keys())}")
            if 'popular' in results['perfect']:
                print(f"  Perfect popular count: {len(results['perfect']['popular'])}")
            if 'technical' in results['perfect']:
                print(f"  Perfect technical count: {len(results['perfect']['technical'])}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_search_execution()

