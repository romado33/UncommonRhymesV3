"""
Debug script to check phonetic keys generation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.phonetics import parse_pron, k_keys
from rhyme_core.engine import get_pronunciation_from_db

def debug_phonetic_keys():
    """Debug phonetic keys generation"""
    
    target_word = "table"
    
    print(f"Debugging phonetic keys for '{target_word}'")
    print("="*60)
    
    # Get pronunciation
    pron = get_pronunciation_from_db(target_word)
    print(f"Pronunciation: {pron}")
    
    if not pron:
        print("ERROR: No pronunciation found")
        return
    
    # Parse pronunciation
    phones = parse_pron(pron)
    print(f"Parsed phones: {phones}")
    
    if not phones:
        print("ERROR: No phones parsed")
        return
    
    # Generate keys
    try:
        k1, k2, k3 = k_keys(phones)
        print(f"K1: {k1}")
        print(f"K2: {k2}")
        print(f"K3: {k3}")
    except Exception as e:
        print(f"ERROR generating keys: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_phonetic_keys()