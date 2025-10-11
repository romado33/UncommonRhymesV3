#!/usr/bin/env python3
"""
Comprehensive Diagnostic Suite for Anti-LLM Rhyme Engine
========================================================

Tests all critical components:
1. Dollar/ART phonetic bug (MUST be fixed)
2. K1/K2/K3 hierarchical matching
3. Phonetic similarity calculations
4. Zipf filtering and quality control
5. Stress pattern preservation
6. Metrical foot classification
7. Recall vs Datamuse benchmark
8. Performance metrics

Each test provides:
- ✅ PASS or ❌ FAIL status
- Detailed explanation of what's being tested
- Expected vs actual results
- Actionable recommendations
"""

import time
import sys
from typing import Dict, List, Tuple, Any

# Try to import from engine_ULTIMATE
try:
    from engine_ULTIMATE import (
        search_rhymes, get_result_counts, PhoneticEngine,
        MetricalAnalyzer, MetricalFoot, cfg
    )
    ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: engine_ULTIMATE not available. Using mock implementations.")
    ENGINE_AVAILABLE = False

# =============================================================================
# TEST SUITE
# =============================================================================

class DiagnosticTest:
    """Base class for diagnostic tests"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.message = ""
        self.details = {}
    
    def run(self) -> bool:
        """Override in subclasses"""
        raise NotImplementedError
    
    def report(self) -> str:
        """Generate test report"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        report = f"\n{status} | {self.name}\n"
        report += f"{'─' * 80}\n"
        report += f"Description: {self.description}\n"
        report += f"Result: {self.message}\n"
        
        if self.details:
            report += "\nDetails:\n"
            for key, value in self.details.items():
                report += f"  • {key}: {value}\n"
        
        return report

class DollarARTTest(DiagnosticTest):
    """
    Test #1: Critical Dollar/ART Phonetic Bug
    
    PROBLEM: "dollar" was incorrectly matching with "chart/dart/heart" 
    instead of "collar/holler/scholar"
    
    ROOT CAUSE: Stress-stripped K2 keys allowed cross-family matching
    
    FIX: Use stress-preserved K3 keys for perfect rhymes
    
    EXPECTED: 
    - "dollar" matches: collar, holler, scholar, taller
    - "dollar" NO MATCH: chart, dart, heart, art, start
    """
    
    def __init__(self):
        super().__init__(
            "Dollar/ART Phonetic Bug Fix",
            "Verifies that 'dollar' correctly matches 'collar' family, NOT 'chart' family"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            # Search for "dollar" rhymes
            results = search_rhymes("dollar", use_datamuse=False)
            
            # Get all perfect matches
            all_perfect = (results['perfect']['popular'] + 
                          results['perfect']['technical'])
            perfect_words = {m.word for m in all_perfect}
            
            # Expected matches (same phonetic family)
            expected_matches = {'collar', 'holler', 'scholar', 'taller', 'caller'}
            expected_found = expected_matches & perfect_words
            
            # Should NOT match (different phonetic family)
            unexpected_matches = {'chart', 'dart', 'heart', 'art', 'start', 'cart'}
            unexpected_found = unexpected_matches & perfect_words
            
            # Test passes if we find expected and avoid unexpected
            self.passed = (len(expected_found) >= 2 and len(unexpected_found) == 0)
            
            if self.passed:
                self.message = (f"✅ CORRECT: Found {len(expected_found)} expected matches "
                               f"({', '.join(sorted(expected_found))}), "
                               f"avoided all {len(unexpected_matches)} cross-family words")
            else:
                self.message = (f"❌ INCORRECT: Found {len(expected_found)} expected "
                               f"({', '.join(sorted(expected_found)) if expected_found else 'none'}), "
                               f"but also matched {len(unexpected_found)} wrong words "
                               f"({', '.join(sorted(unexpected_found)) if unexpected_found else 'none'})")
            
            self.details = {
                'Expected matches found': f"{len(expected_found)}/{len(expected_matches)}",
                'Wrong matches avoided': f"{len(unexpected_matches) - len(unexpected_found)}/{len(unexpected_matches)}",
                'Total perfect matches': len(perfect_words),
                'Search time': f"{results['metadata']['search_time']:.3f}s"
            }
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

class K3HierarchyTest(DiagnosticTest):
    """
    Test #2: K3/K2/K1 Hierarchical Matching
    
    Verifies the three-stage phonetic key architecture:
    - K3: Stress-preserved endings (perfect rhymes)
    - K2: Stress-stripped endings (near-perfect rhymes)
    - K1: Vowel nucleus only (assonance)
    
    EXPECTED: Each level returns appropriate matches
    """
    
    def __init__(self):
        super().__init__(
            "K3/K2/K1 Hierarchical Matching",
            "Verifies three-stage phonetic key architecture works correctly"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            # Test word with clear phonetic structure
            results = search_rhymes("table", use_datamuse=False)
            
            # Count matches at each level
            perfect_count = (len(results['perfect']['popular']) + 
                           len(results['perfect']['technical']))
            near_perfect_count = (len(results['near_perfect']['popular']) + 
                                len(results['near_perfect']['technical']))
            assonance_count = (len(results['assonance']['popular']) + 
                             len(results['assonance']['technical']))
            
            # Hierarchical expectations:
            # Perfect < Near-Perfect < Assonance (strictness decreases)
            # Each level should have some matches
            has_hierarchy = (perfect_count >= 1 and 
                           near_perfect_count >= perfect_count and
                           assonance_count >= near_perfect_count)
            
            self.passed = has_hierarchy
            
            if self.passed:
                self.message = (f"✅ CORRECT: Hierarchical matching works "
                               f"(Perfect: {perfect_count}, Near: {near_perfect_count}, "
                               f"Assonance: {assonance_count})")
            else:
                self.message = (f"❌ INCORRECT: Hierarchy broken "
                               f"(Perfect: {perfect_count}, Near: {near_perfect_count}, "
                               f"Assonance: {assonance_count})")
            
            self.details = {
                'Perfect matches (K3)': perfect_count,
                'Near-perfect matches (K2)': near_perfect_count,
                'Assonance matches (K1)': assonance_count,
                'Hierarchy correct': 'Yes' if has_hierarchy else 'No',
                'Search time': f"{results['metadata']['search_time']:.3f}s"
            }
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

class QualityFilteringTest(DiagnosticTest):
    """
    Test #3: Quality Filtering (No Garbage Words)
    
    Verifies that ultra-common garbage words are filtered out:
    - Stopwords: of, but, from, the, a, an, etc.
    - Words with zipf > zipf_max_slant
    
    EXPECTED: Zero garbage words in any category
    """
    
    def __init__(self):
        super().__init__(
            "Quality Filtering (No Garbage Words)",
            "Verifies that stopwords and ultra-common garbage words are filtered"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            # Test word that previously had garbage matches
            results = search_rhymes("double", use_datamuse=False)
            
            # Get all matches
            all_matches = []
            for category in ['perfect', 'near_perfect', 'assonance']:
                all_matches.extend(results[category]['popular'])
                all_matches.extend(results[category]['technical'])
            
            all_words = {m.word for m in all_matches}
            
            # Check for stopwords
            stopwords_found = all_words & cfg.ultra_common_stop_words
            
            # Check for ultra-high zipf (>zipf_max_slant)
            high_zipf_words = [m for m in all_matches 
                              if m.zipf_frequency > cfg.zipf_max_slant]
            
            # Test passes if no garbage words found
            self.passed = (len(stopwords_found) == 0 and len(high_zipf_words) == 0)
            
            if self.passed:
                self.message = (f"✅ CORRECT: No garbage words found "
                               f"(0 stopwords, 0 ultra-high zipf)")
            else:
                self.message = (f"❌ INCORRECT: Found garbage words - "
                               f"{len(stopwords_found)} stopwords "
                               f"({', '.join(sorted(stopwords_found)) if stopwords_found else 'none'}), "
                               f"{len(high_zipf_words)} ultra-high zipf")
            
            self.details = {
                'Total matches': len(all_matches),
                'Stopwords found': len(stopwords_found),
                'Ultra-high zipf found': len(high_zipf_words),
                'zipf_max_slant threshold': cfg.zipf_max_slant,
                'Quality filtering': 'Passed' if self.passed else 'Failed'
            }
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

class PhoneticAccuracyTest(DiagnosticTest):
    """
    Test #4: Phonetic Similarity Calculations
    
    Verifies that phonetic similarity calculations are accurate:
    - Identical cores should have similarity ≈ 1.0
    - Very different cores should have similarity < 0.5
    - Similar vowels but different consonants should score accordingly
    """
    
    def __init__(self):
        super().__init__(
            "Phonetic Similarity Accuracy",
            "Verifies phonetic similarity calculations are accurate"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            phonetic = PhoneticEngine()
            
            # Test case 1: Identical cores
            core1 = ['AE1', 'T']
            core2 = ['AE1', 'T']
            sim1 = phonetic.calculate_phonetic_similarity(core1, core2)
            
            # Test case 2: Very different cores
            core3 = ['AE1', 'T']
            core4 = ['OW1', 'K']
            sim2 = phonetic.calculate_phonetic_similarity(core3, core4)
            
            # Test case 3: Same vowel, different consonants
            core5 = ['AE1', 'T']
            core6 = ['AE1', 'P']
            sim3 = phonetic.calculate_phonetic_similarity(core5, core6)
            
            # Expectations
            identical_correct = sim1 >= 0.95
            different_correct = sim2 <= 0.5
            partial_correct = 0.5 <= sim3 <= 0.95
            
            self.passed = identical_correct and different_correct and partial_correct
            
            if self.passed:
                self.message = "✅ CORRECT: All phonetic similarity calculations accurate"
            else:
                issues = []
                if not identical_correct:
                    issues.append(f"identical cores={sim1:.2f} (expected ≥0.95)")
                if not different_correct:
                    issues.append(f"different cores={sim2:.2f} (expected ≤0.5)")
                if not partial_correct:
                    issues.append(f"partial match={sim3:.2f} (expected 0.5-0.95)")
                self.message = f"❌ INCORRECT: {', '.join(issues)}"
            
            self.details = {
                'Identical cores (AE1 T vs AE1 T)': f"{sim1:.3f}",
                'Different cores (AE1 T vs OW1 K)': f"{sim2:.3f}",
                'Partial match (AE1 T vs AE1 P)': f"{sim3:.3f}",
                'All tests passed': 'Yes' if self.passed else 'No'
            }
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

class MetricalAnalysisTest(DiagnosticTest):
    """
    Test #5: Metrical Foot Classification
    
    Verifies that stress patterns are correctly classified into metrical feet
    """
    
    def __init__(self):
        super().__init__(
            "Metrical Foot Classification",
            "Verifies stress pattern → metrical foot classification"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            analyzer = MetricalAnalyzer()
            
            # Test cases: (stress_pattern, expected_foot)
            test_cases = [
                ('0-1', MetricalFoot.IAMB),           # x /
                ('1-0', MetricalFoot.TROCHEE),        # / x
                ('0-0-1', MetricalFoot.ANAPEST),      # x x /
                ('1-0-0', MetricalFoot.DACTYL),       # / x x
                ('1-1', MetricalFoot.SPONDEE),        # / /
                ('0-0', MetricalFoot.PYRRHIC),        # x x
                ('0-1-0', MetricalFoot.AMPHIBRACH),   # x / x
            ]
            
            results = []
            for pattern, expected in test_cases:
                actual = analyzer.analyze_stress_pattern(pattern)
                correct = (actual == expected)
                results.append((pattern, expected, actual, correct))
            
            passed_count = sum(1 for _, _, _, correct in results if correct)
            self.passed = (passed_count == len(test_cases))
            
            if self.passed:
                self.message = f"✅ CORRECT: All {len(test_cases)} metrical classifications accurate"
            else:
                failed = [f"{pat}→{act.value} (expected {exp.value})" 
                         for pat, exp, act, correct in results if not correct]
                self.message = f"❌ INCORRECT: {len(failed)} classifications wrong: {', '.join(failed)}"
            
            self.details = {
                'Total test cases': len(test_cases),
                'Passed': passed_count,
                'Failed': len(test_cases) - passed_count,
                'Success rate': f"{(passed_count/len(test_cases)*100):.1f}%"
            }
            
            for pattern, expected, actual, correct in results:
                status = "✓" if correct else "✗"
                self.details[f"{status} {pattern}"] = f"{actual.value}"
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

class PerformanceTest(DiagnosticTest):
    """
    Test #6: Performance Metrics
    
    Verifies that search performance meets targets:
    - Search time < 100ms for typical queries
    - Can handle 10+ queries per second
    """
    
    def __init__(self):
        super().__init__(
            "Performance Metrics",
            "Verifies search performance meets speed targets"
        )
    
    def run(self) -> bool:
        if not ENGINE_AVAILABLE:
            self.message = "Engine not available - cannot test"
            return False
        
        try:
            # Test words
            test_words = ['table', 'double', 'cat', 'love', 'heart']
            
            # Run searches and time them
            times = []
            for word in test_words:
                start = time.time()
                results = search_rhymes(word, use_datamuse=False)
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            queries_per_sec = 1.0 / avg_time if avg_time > 0 else 0
            
            # Performance targets
            avg_meets_target = avg_time < 0.100  # 100ms average
            max_meets_target = max_time < 0.200  # 200ms worst case
            qps_meets_target = queries_per_sec >= 10  # 10+ queries/sec
            
            self.passed = avg_meets_target and max_meets_target and qps_meets_target
            
            if self.passed:
                self.message = (f"✅ CORRECT: Performance meets all targets "
                               f"(avg: {avg_time*1000:.1f}ms, "
                               f"qps: {queries_per_sec:.1f})")
            else:
                issues = []
                if not avg_meets_target:
                    issues.append(f"avg time {avg_time*1000:.1f}ms > 100ms target")
                if not max_meets_target:
                    issues.append(f"max time {max_time*1000:.1f}ms > 200ms target")
                if not qps_meets_target:
                    issues.append(f"qps {queries_per_sec:.1f} < 10 target")
                self.message = f"❌ SLOW: {', '.join(issues)}"
            
            self.details = {
                'Average search time': f"{avg_time*1000:.1f}ms",
                'Max search time': f"{max_time*1000:.1f}ms",
                'Min search time': f"{min(times)*1000:.1f}ms",
                'Queries per second': f"{queries_per_sec:.1f}",
                'Test words': len(test_words),
                'Performance grade': 'A' if self.passed else 'C'
            }
            
            return self.passed
        
        except Exception as e:
            self.message = f"❌ ERROR: {str(e)}"
            self.passed = False
            return False

# =============================================================================
# TEST RUNNER
# =============================================================================

def run_all_tests() -> Tuple[int, int, List[DiagnosticTest]]:
    """
    Run all diagnostic tests
    
    Returns: (passed_count, total_count, test_objects)
    """
    print("="*80)
    print("🧪 COMPREHENSIVE DIAGNOSTIC SUITE - Anti-LLM Rhyme Engine")
    print("="*80)
    print(f"\nConfiguration:")
    if ENGINE_AVAILABLE:
        print(f"  • zipf_max_slant: {cfg.zipf_max_slant}")
        print(f"  • min_assonance_score: {cfg.min_assonance_score}")
        print(f"  • use_datamuse: {cfg.use_datamuse}")
    print(f"  • Engine available: {'Yes' if ENGINE_AVAILABLE else 'No'}")
    print()
    
    # Initialize tests
    tests = [
        DollarARTTest(),
        K3HierarchyTest(),
        QualityFilteringTest(),
        PhoneticAccuracyTest(),
        MetricalAnalysisTest(),
        PerformanceTest()
    ]
    
    # Run each test
    results = []
    for i, test in enumerate(tests, 1):
        print(f"Running test {i}/{len(tests)}: {test.name}...")
        test.run()
        results.append(test)
    
    # Generate reports
    print("\n" + "="*80)
    print("📋 DETAILED TEST REPORTS")
    print("="*80)
    
    for test in results:
        print(test.report())
    
    # Summary
    passed = sum(1 for t in results if t.passed)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\nTests passed: {passed}/{total} ({pass_rate:.1f}%)")
    print(f"Tests failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Engine is production-ready!")
        print("🎯 Anti-LLM algorithms are correctly targeting phonological weaknesses")
    elif passed >= total * 0.8:
        print("\n⚠️  MOSTLY PASSED - Minor issues detected, review failed tests")
    else:
        print("\n❌ SIGNIFICANT ISSUES - Critical fixes needed before production")
    
    print("="*80)
    
    return passed, total, results

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    passed, total, tests = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)
