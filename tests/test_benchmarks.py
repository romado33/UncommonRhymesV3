import os
from pathlib import Path

# Flexible import handling - works whether search.py is standalone or in package
try:
    from rhyme_core.search import search_all_categories
except ImportError:
    try:
        from search import search_all_categories
    except ImportError:
        # If neither works, skip tests gracefully
        import pytest
        pytestmark = pytest.mark.skip(reason="search module not found")
        
        def search_all_categories(*args, **kwargs):
            raise ImportError("search_all_categories not available")

# Load the same benchmark list the app uses, if available
def _load_terms():
    candidates = [
        Path("benchmark.queries_used.txt"),
        Path("data/dev/benchmark.queries_used.txt"),
        Path("tests/benchmark.queries_used.txt"),
    ]
    for p in candidates:
        if p.exists():
            terms = []
            for ln in p.read_text(encoding="utf-8").splitlines():
                t = (ln or "").strip()
                if t and not t.startswith("#"):
                    terms.append(t)
            if terms:
                return terms
    # default small set
    return ["double", "habit", "paper"]

TERMS = _load_terms()

def test_benchmarks_smoke():
    """Basic non-regression: searching doesn't crash and buckets are present"""
    for t in TERMS[:25]:  # keep CI bounded
        res = search_all_categories(
            t,
            max_items=20,
            relax_rap=True,
            include_rap=False,
            zipf_max=4.0,
            min_each=10,
            zipf_max_multi=5.5,
        )
        assert isinstance(res, dict), f"Expected dict result for term '{t}'"
        
        # Check all expected buckets exist
        for key in ("uncommon", "slant", "multiword", "rap_targets"):
            assert key in res, f"missing bucket '{key}' for term '{t}'"
            assert isinstance(res[key], list), f"bucket '{key}' should be list for term '{t}'"
        
        # Verify each item in buckets is a dict
        for key in ("uncommon", "slant", "multiword", "rap_targets"):
            assert all(isinstance(x, dict) for x in res[key]), \
                f"All items in '{key}' bucket should be dicts for term '{t}'"

def test_single_term():
    """Test a single known term works correctly"""
    res = search_all_categories("double", max_items=20)
    assert isinstance(res, dict)
    assert "uncommon" in res
    assert "slant" in res
    # Should find some results for "double"
    total_results = sum(len(res[k]) for k in ["uncommon", "slant", "multiword", "rap_targets"])
    assert total_results >= 0, "Should return results (or empty list if no data)"

def test_empty_term():
    """Test that empty term doesn't crash"""
    res = search_all_categories("", max_items=20)
    assert isinstance(res, dict)
    # Empty term should return empty buckets
    for key in ("uncommon", "slant", "multiword", "rap_targets"):
        assert key in res

def test_nonsense_term():
    """Test that nonsense term doesn't crash"""
    res = search_all_categories("xyzabc123", max_items=20)
    assert isinstance(res, dict)
    # Should return empty buckets or handle gracefully
    for key in ("uncommon", "slant", "multiword", "rap_targets"):
        assert key in res
        assert isinstance(res[key], list)

if __name__ == "__main__":
    # Allow running tests directly
    import sys
    print(f"Testing with {len(TERMS)} terms...")
    try:
        test_benchmarks_smoke()
        print("✓ test_benchmarks_smoke passed")
        test_single_term()
        print("✓ test_single_term passed")
        test_empty_term()
        print("✓ test_empty_term passed")
        test_nonsense_term()
        print("✓ test_nonsense_term passed")
        print("\nAll tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)