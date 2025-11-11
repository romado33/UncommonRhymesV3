"""
Comprehensive test of the fixed rhyme search system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, cfg
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def comprehensive_test():
    """Run comprehensive test of the rhyme search system"""
    
    test_words = ["table", "without", "sister", "time", "home"]
    
    print("Comprehensive Rhyme Search Test")
    print("="*60)
    
    for target_word in test_words:
        print(f"\nTesting '{target_word}':")
        print("-" * 40)
        
        try:
            results = search_rhymes(target_word, use_datamuse=True)
            
            # Count results
            perfect_popular = len(results.get('perfect', {}).get('popular', []))
            perfect_technical = len(results.get('perfect', {}).get('technical', []))
            total_perfect = perfect_popular + perfect_technical
            
            near_perfect_popular = len(results.get('slant', {}).get('near_perfect', {}).get('popular', []))
            near_perfect_technical = len(results.get('slant', {}).get('near_perfect', {}).get('technical', []))
            total_near_perfect = near_perfect_popular + near_perfect_technical
            
            assonance_popular = len(results.get('slant', {}).get('assonance', {}).get('popular', []))
            assonance_technical = len(results.get('slant', {}).get('assonance', {}).get('technical', []))
            total_assonance = assonance_popular + assonance_technical
            
            colloquial = len(results.get('colloquial', []))
            
            print(f"  Perfect rhymes: {total_perfect} ({perfect_popular} popular, {perfect_technical} technical)")
            print(f"  Near-perfect: {total_near_perfect} ({near_perfect_popular} popular, {near_perfect_technical} technical)")
            print(f"  Assonance: {total_assonance} ({assonance_popular} popular, {assonance_technical} technical)")
            print(f"  Multi-word: {colloquial}")
            
            # Show some examples
            if perfect_popular > 0:
                examples = [w['word'] for w in results['perfect']['popular'][:5]]
                print(f"  Popular perfect examples: {examples}")
            
            if perfect_technical > 0:
                examples = [w['word'] for w in results['perfect']['technical'][:3]]
                print(f"  Technical perfect examples: {examples}")
            
            # Check metadata
            if 'metadata' in results:
                metadata = results['metadata']
                print(f"  Metadata keys: {list(metadata.keys())}")
                if 'datamuse_calls' in metadata:
                    print(f"  Datamuse calls: {metadata['datamuse_calls']}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Test completed!")

if __name__ == "__main__":
    comprehensive_test()




