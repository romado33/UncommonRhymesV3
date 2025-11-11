"""
Debug script to add comprehensive logging to search_rhymes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_search_with_logging():
    """Debug search_rhymes with comprehensive logging"""
    
    config = cfg
    target_word = "table"
    
    print(f"Debugging search_rhymes with logging for '{target_word}'")
    print("="*60)
    
    # Add debug logging to the search_rhymes function
    import rhyme_core.engine
    
    # Monkey patch the search_rhymes function to add logging
    original_search_rhymes = rhyme_core.engine.search_rhymes
    
    def logged_search_rhymes(target_word, use_datamuse=True, **kwargs):
        print(f"DEBUG: search_rhymes called with use_datamuse={use_datamuse}")
        
        # Call the original function
        result = original_search_rhymes(target_word, use_datamuse=use_datamuse, **kwargs)
        
        # Log the result
        print(f"DEBUG: search_rhymes returned:")
        print(f"  Keys: {list(result.keys())}")
        
        if 'metadata' in result:
            print(f"  Metadata: {result['metadata']}")
        else:
            print(f"  No metadata found")
        
        if 'perfect' in result:
            perfect = result['perfect']
            print(f"  Perfect rhymes:")
            print(f"    Popular: {len(perfect.get('popular', []))}")
            print(f"    Technical: {len(perfect.get('technical', []))}")
            
            if perfect.get('popular'):
                print(f"    Popular words: {[w['word'] for w in perfect['popular'][:5]]}")
            if perfect.get('technical'):
                print(f"    Technical words: {[w['word'] for w in perfect['technical'][:5]]}")
        
        return result
    
    # Replace the function
    rhyme_core.engine.search_rhymes = logged_search_rhymes
    
    try:
        # Run the search
        results = search_rhymes(target_word, use_datamuse=True)
        
        print(f"\nFinal results summary:")
        print(f"  Perfect popular: {len(results.get('perfect', {}).get('popular', []))}")
        print(f"  Perfect technical: {len(results.get('perfect', {}).get('technical', []))}")
        
    finally:
        # Restore the original function
        rhyme_core.engine.search_rhymes = original_search_rhymes

if __name__ == "__main__":
    debug_search_with_logging()




