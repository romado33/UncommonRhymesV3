"""
Debug script to investigate filter consistency issues
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes
from rhyme_core.config import PrecisionConfig

def debug_filter_consistency():
    """Debug why the same search gives different results"""
    
    config = PrecisionConfig()
    target_word = "table"
    
    print(f"Testing filter consistency for '{target_word}'")
    print("="*60)
    
    # Test 1: Default settings
    print("Test 1: Default settings")
    results1 = search_rhymes(target_word, config)
    
    perfect_pop1 = len(results1.get('perfect', {}).get('popular', []))
    perfect_tech1 = len(results1.get('perfect', {}).get('technical', []))
    near_pop1 = len(results1.get('slant', {}).get('near_perfect', {}).get('popular', []))
    near_tech1 = len(results1.get('slant', {}).get('near_perfect', {}).get('technical', []))
    assonance_pop1 = len(results1.get('slant', {}).get('assonance', {}).get('popular', []))
    assonance_tech1 = len(results1.get('slant', {}).get('assonance', {}).get('technical', []))
    colloquial1 = len(results1.get('colloquial', []))
    
    print(f"  Perfect: {perfect_pop1} popular, {perfect_tech1} technical")
    print(f"  Near-perfect: {near_pop1} popular, {near_tech1} technical")
    print(f"  Assonance: {assonance_pop1} popular, {assonance_tech1} technical")
    print(f"  Colloquial: {colloquial1}")
    
    # Test 2: Same settings again
    print("\nTest 2: Same settings again")
    results2 = search_rhymes(target_word, config)
    
    perfect_pop2 = len(results2.get('perfect', {}).get('popular', []))
    perfect_tech2 = len(results2.get('perfect', {}).get('technical', []))
    near_pop2 = len(results2.get('slant', {}).get('near_perfect', {}).get('popular', []))
    near_tech2 = len(results2.get('slant', {}).get('near_perfect', {}).get('technical', []))
    assonance_pop2 = len(results2.get('slant', {}).get('assonance', {}).get('popular', []))
    assonance_tech2 = len(results2.get('slant', {}).get('assonance', {}).get('technical', []))
    colloquial2 = len(results2.get('colloquial', []))
    
    print(f"  Perfect: {perfect_pop2} popular, {perfect_tech2} technical")
    print(f"  Near-perfect: {near_pop2} popular, {near_tech2} technical")
    print(f"  Assonance: {assonance_pop2} popular, {assonance_tech2} technical")
    print(f"  Colloquial: {colloquial2}")
    
    # Check if results are consistent
    print("\nConsistency Check:")
    perfect_consistent = (perfect_pop1 == perfect_pop2 and perfect_tech1 == perfect_tech2)
    near_consistent = (near_pop1 == near_pop2 and near_tech1 == near_tech2)
    assonance_consistent = (assonance_pop1 == assonance_pop2 and assonance_tech1 == assonance_tech2)
    colloquial_consistent = (colloquial1 == colloquial2)
    
    print(f"  Perfect rhymes consistent: {perfect_consistent}")
    print(f"  Near-perfect rhymes consistent: {near_consistent}")
    print(f"  Assonance rhymes consistent: {assonance_consistent}")
    print(f"  Colloquial rhymes consistent: {colloquial_consistent}")
    
    if not (perfect_consistent and near_consistent and assonance_consistent and colloquial_consistent):
        print("\nX INCONSISTENCY DETECTED!")
        print("The same search parameters are producing different results.")
        
        # Show differences
        if not perfect_consistent:
            print(f"  Perfect rhymes changed: {perfect_pop1}→{perfect_pop2} popular, {perfect_tech1}→{perfect_tech2} technical")
        if not near_consistent:
            print(f"  Near-perfect rhymes changed: {near_pop1}→{near_pop2} popular, {near_tech1}→{near_tech2} technical")
        if not assonance_consistent:
            print(f"  Assonance rhymes changed: {assonance_pop1}→{assonance_pop2} popular, {assonance_tech1}→{assonance_tech2} technical")
        if not colloquial_consistent:
            print(f"  Colloquial rhymes changed: {colloquial1}→{colloquial2}")
    else:
        print("\n[OK] Results are consistent")
    
    # Test 3: Check if it's related to the uncommon filter
    print("\nTest 3: Checking uncommon filter behavior")
    
    # Look at the metadata to see what's happening
    metadata1 = results1.get('metadata', {})
    metadata2 = results2.get('metadata', {})
    
    print(f"  Search time 1: {metadata1.get('search_time_ms', 0)}ms")
    print(f"  Search time 2: {metadata2.get('search_time_ms', 0)}ms")
    print(f"  CMU results 1: {metadata1.get('cmu_results_count', 0)}")
    print(f"  CMU results 2: {metadata2.get('cmu_results_count', 0)}")
    print(f"  Datamuse results 1: {metadata1.get('datamuse_results_count', 0)}")
    print(f"  Datamuse results 2: {metadata2.get('datamuse_results_count', 0)}")

if __name__ == "__main__":
    debug_filter_consistency()
