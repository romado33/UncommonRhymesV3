"""
FIX #1: CORRECTED PHONETIC VALIDATION TEST FOR BENCHMARK
=========================================================

Problem: The benchmark was checking if `dollar k1 ≠ chart k1`, but this is WRONG!
Both words SHOULD have the same K1 (vowel nucleus = AA).

Root Cause Understanding:
- dollar: D AA1 L ER0 → vowel nucleus = AA, coda = L
- chart:  CH AA1 R T → vowel nucleus = AA, coda = R

They SHARE the same vowel (K1 = AA) but have DIFFERENT codas (L vs R).
The phonetic families are separated by CODA, not by K1!

Correct Fix:
Instead of checking K1 values directly, we test that the search engine
properly separates phonetic families by checking actual rhyme results:
- "dollar" should find: collar, holler, scholar (all have AA + L)
- "chart" should find: dart, heart, smart (all have AA + R)
- NO CROSS-CONTAMINATION: dollar results should NOT include chart family words!

This patch replaces the incorrect phonetic validation with the correct one.
"""

def validate_phonetic_separation_FIXED(search_engine, test_results_dict):
    """
    CORRECTED phonetic validation test.
    
    Tests that phonetic families are properly separated by checking
    actual search results, not K1 values.
    
    Args:
        search_engine: Your search engine instance with search_all_categories() method
        test_results_dict: Dict mapping query words to their search results
        
    Returns:
        dict: {
            'passed': bool,
            'dollar_family_correct': bool,
            'chart_family_correct': bool,
            'no_contamination': bool,
            'details': str
        }
    """
    
    # Expected phonetic families
    DOLLAR_FAMILY = {'dollar', 'collar', 'holler', 'scholar', 'squalor'}
    CHART_FAMILY = {'chart', 'dart', 'heart', 'smart', 'art', 'start', 'part', 'cart'}
    
    results = {
        'passed': False,
        'dollar_family_correct': False,
        'chart_family_correct': False,
        'no_contamination': False,
        'details': ''
    }
    
    # Get search results for 'dollar'
    if 'dollar' not in test_results_dict:
        # Run search if not already in results
        dollar_results = search_engine.search_all_categories('dollar')
    else:
        dollar_results = test_results_dict['dollar']
    
    # Get search results for 'chart'
    if 'chart' not in test_results_dict:
        chart_results = search_engine.search_all_categories('chart')
    else:
        chart_results = test_results_dict['chart']
    
    # Extract words from results (handle different result structures)
    dollar_words = set()
    chart_words = set()
    
    # Handle dict with categories: {"uncommon": [...], "slant": [...], "multiword": [...]}
    if isinstance(dollar_results, dict):
        for category in ['uncommon', 'slant', 'multiword']:
            if category in dollar_results:
                dollar_words.update([w.lower().strip() for w in dollar_results[category] if w])
    elif isinstance(dollar_results, list):
        dollar_words = set([w.lower().strip() for w in dollar_results if w])
    
    if isinstance(chart_results, dict):
        for category in ['uncommon', 'slant', 'multiword']:
            if category in chart_results:
                chart_words.update([w.lower().strip() for w in chart_results[category] if w])
    elif isinstance(chart_results, list):
        chart_words = set([w.lower().strip() for w in chart_results if w])
    
    # TEST 1: Dollar should find its family members
    dollar_found = dollar_words.intersection(DOLLAR_FAMILY)
    results['dollar_family_correct'] = len(dollar_found) >= 2  # At least 2 family members
    
    # TEST 2: Chart should find its family members
    chart_found = chart_words.intersection(CHART_FAMILY)
    results['chart_family_correct'] = len(chart_found) >= 2  # At least 2 family members
    
    # TEST 3: NO CROSS-CONTAMINATION (most critical!)
    # Dollar results should NOT contain chart family words
    dollar_contaminated = dollar_words.intersection(CHART_FAMILY)
    # Chart results should NOT contain dollar family words
    chart_contaminated = chart_words.intersection(DOLLAR_FAMILY)
    
    results['no_contamination'] = (len(dollar_contaminated) == 0) and (len(chart_contaminated) == 0)
    
    # Overall pass: all three tests must pass
    results['passed'] = (
        results['dollar_family_correct'] and 
        results['chart_family_correct'] and 
        results['no_contamination']
    )
    
    # Build detailed report
    details = []
    details.append("=== PHONETIC FAMILY SEPARATION TEST ===\n")
    details.append(f"Dollar family found: {dollar_found}")
    details.append(f"  ✓ Correct: {results['dollar_family_correct']}\n")
    
    details.append(f"Chart family found: {chart_found}")
    details.append(f"  ✓ Correct: {results['chart_family_correct']}\n")
    
    if dollar_contaminated:
        details.append(f"❌ CONTAMINATION: Dollar results include chart family: {dollar_contaminated}")
    if chart_contaminated:
        details.append(f"❌ CONTAMINATION: Chart results include dollar family: {chart_contaminated}")
    
    if results['no_contamination']:
        details.append("✓ No cross-contamination detected\n")
    
    details.append(f"\nOverall: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
    
    results['details'] = '\n'.join(details)
    
    return results


def validate_k_key_generation_CORRECT(phonetics_module):
    """
    EDUCATIONAL TEST: Shows that dollar and chart SHOULD have same K1.
    
    This is NOT a bug - it's correct phonetic representation!
    Both words have the AA vowel, so K1 should be identical.
    They differ in their CODA (tail), which affects K2/K3.
    
    Args:
        phonetics_module: Your phonetics.py module with k_keys() function
        
    Returns:
        dict: Educational information about K-key generation
    """
    
    test_words = {
        'dollar': ['D', 'AA1', 'L', 'ER0'],
        'collar': ['K', 'AA1', 'L', 'ER0'],
        'chart': ['CH', 'AA1', 'R', 'T'],
        'dart': ['D', 'AA1', 'R', 'T']
    }
    
    results = {
        'k_keys': {},
        'analysis': [],
        'verdict': ''
    }
    
    # Get K-keys for all test words
    for word, phonemes in test_words.items():
        k1, k2, k3 = phonetics_module.k_keys(phonemes)
        results['k_keys'][word] = {
            'k1': k1,
            'k2': k2,
            'k3': k3,
            'phonemes': phonemes
        }
    
    # Analyze results
    results['analysis'].append("=== K-KEY GENERATION ANALYSIS ===\n")
    
    # K1 Analysis (vowel nucleus)
    results['analysis'].append("K1 (Vowel Nucleus):")
    results['analysis'].append(f"  dollar K1: {results['k_keys']['dollar']['k1']}")
    results['analysis'].append(f"  chart K1:  {results['k_keys']['chart']['k1']}")
    
    if results['k_keys']['dollar']['k1'] == results['k_keys']['chart']['k1']:
        results['analysis'].append("  ✅ CORRECT: Same K1 (both have AA vowel)\n")
    else:
        results['analysis'].append("  ❌ ERROR: K1 should be identical!\n")
    
    # K2 Analysis (vowel + tail)
    results['analysis'].append("K2 (Vowel + Coda):")
    results['analysis'].append(f"  dollar K2: {results['k_keys']['dollar']['k2']} (AA + L)")
    results['analysis'].append(f"  chart K2:  {results['k_keys']['chart']['k2']} (AA + R)")
    
    if results['k_keys']['dollar']['k2'] != results['k_keys']['chart']['k2']:
        results['analysis'].append("  ✅ CORRECT: Different K2 (different codas)\n")
    else:
        results['analysis'].append("  ❌ ERROR: K2 should be different!\n")
    
    # Verdict
    same_k1 = (results['k_keys']['dollar']['k1'] == results['k_keys']['chart']['k1'])
    diff_k2 = (results['k_keys']['dollar']['k2'] != results['k_keys']['chart']['k2'])
    
    if same_k1 and diff_k2:
        results['verdict'] = "✅ K-key generation is CORRECT"
    else:
        results['verdict'] = "❌ K-key generation has ERRORS"
    
    results['analysis'].append(f"\nVERDICT: {results['verdict']}")
    
    return results


# ============================================================================
# INTEGRATION EXAMPLE: How to use this in your benchmark.py
# ============================================================================

"""
Replace the old phonetic validation test in benchmark.py with this:

OLD CODE (WRONG):
-----------------
def validate_phonetics(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT k1 FROM words WHERE word = 'dollar'")
    dollar_k1 = cursor.fetchone()[0]
    
    cursor.execute("SELECT k1 FROM words WHERE word = 'chart'")
    chart_k1 = cursor.fetchone()[0]
    
    # THIS IS WRONG! They should have same K1!
    return dollar_k1 != chart_k1


NEW CODE (CORRECT):
-------------------
from fix_1_benchmark_phonetic_test import validate_phonetic_separation_FIXED

def validate_phonetics(search_engine, test_results):
    # Use actual search results to validate phonetic separation
    validation = validate_phonetic_separation_FIXED(search_engine, test_results)
    
    print(validation['details'])
    
    return validation['passed']
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*70)
    print("This fix corrects the phonetic validation in your benchmark.")
    print("The OLD test was checking K1 values, which is WRONG.")
    print("The NEW test checks actual search results for contamination.")
    print("="*70)
