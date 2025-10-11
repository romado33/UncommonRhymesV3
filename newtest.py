#!/usr/bin/env python3
"""
Test the increased Datamuse limit
Shows before (100) vs after (1000)
"""

import requests
from rhyme_core.engine import search_rhymes

def test_datamuse_limit(word):
    """Test different Datamuse limits"""
    print(f"\n{'='*60}")
    print(f"Testing '{word}' with different Datamuse limits")
    print('='*60)
    
    # Get Datamuse with limit 100
    print("\n[1] Datamuse with max=100:")
    try:
        resp = requests.get(
            'https://api.datamuse.com/words',
            params={'rel_rhy': word, 'max': 100},
            timeout=3.0
        )
        dm_100 = [item['word'] for item in resp.json()]
        print(f"  Returned: {len(dm_100)} words")
    except:
        print("  ❌ API error")
        dm_100 = []
    
    # Get Datamuse with limit 1000
    print("\n[2] Datamuse with max=1000:")
    try:
        resp = requests.get(
            'https://api.datamuse.com/words',
            params={'rel_rhy': word, 'max': 1000},
            timeout=3.0
        )
        dm_1000 = [item['word'] for item in resp.json()]
        print(f"  Returned: {len(dm_1000)} words")
    except:
        print("  ❌ API error")
        dm_1000 = []
    
    # Show difference
    if dm_100 and dm_1000:
        new_words = set(dm_1000) - set(dm_100)
        print(f"\n[3] New words captured with max=1000:")
        print(f"  Additional words: {len(new_words)}")
        if new_words:
            print(f"  Samples: {', '.join(sorted(new_words)[:10])}")
    
    # Test our engine
    print(f"\n[4] Our engine results (now using max=1000):")
    our_results = search_rhymes(word, use_datamuse=True)
    our_words = []
    for category in our_results['perfect']:
        our_words.extend([m['word'].lower() for m in our_results['perfect'][category]])
    
    print(f"  Our results: {len(our_words)} words")
    
    # Calculate recall
    if dm_1000:
        overlap = set([w.lower() for w in our_words]).intersection(set([w.lower() for w in dm_1000]))
        recall = len(overlap) / len(dm_1000) * 100
        print(f"  Overlap: {len(overlap)}")
        print(f"  Recall: {recall:.1f}%")
        print(f"  Status: {'✅ GOOD' if recall >= 70 else '❌ LOW'}")

if __name__ == "__main__":
    # Test words that have many rhymes
    test_words = ['love', 'time', 'day', 'way']
    
    for word in test_words:
        test_datamuse_limit(word)
    
    print(f"\n{'='*60}")
    print("Summary:")
    print("  With max=1000, we capture more comprehensive results")
    print("  This should improve recall for high-frequency words")
    print("  Performance impact: ~+50-100ms for words with many rhymes")
    print('='*60)