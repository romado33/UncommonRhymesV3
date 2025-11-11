"""
Debug script to check if Datamuse is being called
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg

def debug_datamuse_call():
    """Debug if Datamuse is being called"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging Datamuse call for '{target_word}'")
    print("="*60)
    
    # Check config
    print(f"Config use_datamuse: {config.use_datamuse}")
    print(f"Config datamuse_timeout: {config.datamuse_timeout}")
    
    # Run search with explicit use_datamuse=True
    print("\nRunning search with use_datamuse=True")
    results = search_rhymes(target_word, use_datamuse=True)
    
    metadata = results.get('metadata', {})
    print(f"Search metadata:")
    print(f"  datamuse_enabled: {metadata.get('datamuse_enabled', 'Not found')}")
    print(f"  search_time: {metadata.get('search_time', 'Not found')}")
    
    # Check results
    perfect_popular = len(results.get('perfect', {}).get('popular', []))
    perfect_technical = len(results.get('perfect', {}).get('technical', []))
    
    print(f"\nResults:")
    print(f"  Perfect popular: {perfect_popular}")
    print(f"  Perfect technical: {perfect_technical}")
    
    if perfect_popular == 0:
        print("\nX ISSUE: No popular perfect rhymes found!")
        print("This suggests Datamuse is not being called or there's an issue with the merge.")
    else:
        print("\n✓ SUCCESS: Popular perfect rhymes found!")

if __name__ == "__main__":
    debug_datamuse_call()

