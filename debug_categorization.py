"""
Comprehensive debug script to trace the categorization issue
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import search_rhymes, get_phonetic_keys, query_perfect_rhymes
from rhyme_core.config import PrecisionConfig

def debug_categorization_issue():
    """Debug why popular perfect rhymes aren't being categorized correctly"""
    
    config = PrecisionConfig()
    target_word = "table"
    
    print(f"Debugging categorization for '{target_word}'")
    print("="*60)
    
    # Step 1: Check CMU perfect rhymes directly
    print("Step 1: CMU Perfect Rhymes")
    keys = get_phonetic_keys(target_word, config)
    if keys:
        k1, k2, k3 = keys
        print(f"K3 key: {k3}")
        
        cmu_perfect = query_perfect_rhymes(k3, target_word, config)
        print(f"Found {len(cmu_perfect)} CMU perfect rhymes")
        
        popular_count = 0
        technical_count = 0
        
        for word, zipf, word_k1, word_k2, word_k3 in cmu_perfect:
            is_popular = zipf >= 1.5
            if is_popular:
                popular_count += 1
            else:
                technical_count += 1
        
        print(f"  Should be categorized as:")
        print(f"    Popular (zipf >= 1.5): {popular_count}")
        print(f"    Technical (zipf < 1.5): {technical_count}")
    
    print("\n" + "="*60)
    
    # Step 2: Run full search and see what actually gets categorized
    print("Step 2: Full Search Results")
    results = search_rhymes(target_word, config)
    
    perfect_popular = results.get('perfect', {}).get('popular', [])
    perfect_technical = results.get('perfect', {}).get('technical', [])
    
    print(f"Actually categorized as:")
    print(f"  Popular: {len(perfect_popular)}")
    print(f"  Technical: {len(perfect_technical)}")
    
    if perfect_popular:
        print(f"  Popular words: {[item['word'] for item in perfect_popular[:5]]}")
    if perfect_technical:
        print(f"  Technical words: {[item['word'] for item in perfect_technical[:5]]}")
    
    print("\n" + "="*60)
    
    # Step 3: Check if there's a deduplication issue
    print("Step 3: Checking for deduplication issues")
    
    # Get all perfect rhymes from both sources
    all_perfect_words = set()
    all_perfect_words.update(item['word'] for item in perfect_popular)
    all_perfect_words.update(item['word'] for item in perfect_technical)
    
    print(f"Total unique perfect rhymes found: {len(all_perfect_words)}")
    
    # Check if any CMU perfect rhymes are missing
    if keys:
        cmu_words = set(word for word, _, _, _, _ in cmu_perfect)
        missing_words = cmu_words - all_perfect_words
        
        if missing_words:
            print(f"Missing CMU perfect rhymes: {list(missing_words)[:10]}")
        else:
            print("All CMU perfect rhymes are present")
    
    print("\n" + "="*60)
    
    # Step 4: Check Datamuse contribution
    print("Step 4: Datamuse Contribution")
    
    datamuse_perfect = []
    for item in perfect_popular + perfect_technical:
        if item.get('source') == 'datamuse':
            datamuse_perfect.append(item)
    
    print(f"Datamuse perfect rhymes: {len(datamuse_perfect)}")
    
    if datamuse_perfect:
        print(f"Datamuse words: {[item['word'] for item in datamuse_perfect[:5]]}")
    
    print("\n" + "="*60)
    
    # Step 5: Check if the issue is in the merge process
    print("Step 5: Checking merge process")
    
    # Look at the metadata to see what happened
    metadata = results.get('metadata', {})
    print(f"Search metadata:")
    print(f"  CMU results: {metadata.get('cmu_results_count', 0)}")
    print(f"  Datamuse results: {metadata.get('datamuse_results_count', 0)}")
    print(f"  Total before filtering: {metadata.get('total_before_filtering', 0)}")
    print(f"  Total after filtering: {metadata.get('total_after_filtering', 0)}")
    
    # Check if uncommon filter is affecting this
    if 'uncommon_filter_applied' in metadata:
        print(f"  Uncommon filter applied: {metadata['uncommon_filter_applied']}")
        if 'filtering_details' in metadata:
            details = metadata['filtering_details']
            print(f"  Popular items hidden: {details.get('popular_hidden', 0)}")
            print(f"  Technical items hidden: {details.get('technical_hidden', 0)}")

if __name__ == "__main__":
    debug_categorization_issue()

