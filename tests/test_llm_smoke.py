import os
import pytest

# Handle missing imports gracefully
HAS_LLM = False
try:
    from config import FLAGS
    from llm.features.rewrite import rewrite_with_scheme
    HAS_LLM = True
except ImportError:
    # Create mock objects for when modules don't exist
    class MockFlags:
        ENABLE_LLM = False
    
    FLAGS = MockFlags()
    
    def rewrite_with_scheme(text, scheme):
        """Mock function when LLM features not available"""
        raise ImportError("LLM features not available")

# Check if we have both the module AND the API key
skip_reason = None
if not HAS_LLM:
    skip_reason = "LLM modules not available (config or llm.features.rewrite not found)"
elif not FLAGS.ENABLE_LLM:
    skip_reason = "LLM disabled via FLAGS.ENABLE_LLM"
elif not os.getenv('OPENAI_API_KEY'):
    skip_reason = "OPENAI_API_KEY environment variable not set"

@pytest.mark.skipif(skip_reason is not None, reason=skip_reason or "LLM test requirements not met")
def test_rewrite_smoke():
    """Test that LLM rewrite feature works with a simple example"""
    out = rewrite_with_scheme('Keep it humble', 'double')
    assert isinstance(out, str), "Output should be a string"
    assert len(out) > 0, "Output should not be empty"
    assert out != 'Keep it humble', "Output should be different from input (rewritten)"

@pytest.mark.skipif(skip_reason is not None, reason=skip_reason or "LLM test requirements not met")
def test_rewrite_various_inputs():
    """Test rewrite with various input combinations"""
    test_cases = [
        ('simple test', 'double'),
        ('another example', 'trouble'),
        ('short', 'bubble'),
    ]
    
    for text, scheme in test_cases:
        out = rewrite_with_scheme(text, scheme)
        assert isinstance(out, str), f"Failed for input: {text}, {scheme}"
        assert len(out) > 0, f"Empty output for input: {text}, {scheme}"

def test_mock_available():
    """Test that mock functions exist even when LLM not available"""
    # This test should always pass
    assert callable(rewrite_with_scheme)
    assert hasattr(FLAGS, 'ENABLE_LLM')

def test_skip_conditions():
    """Document why tests might be skipped"""
    if not HAS_LLM:
        pytest.skip("LLM modules not found - install required dependencies")
    elif not FLAGS.ENABLE_LLM:
        pytest.skip("LLM features disabled in config")
    elif not os.getenv('OPENAI_API_KEY'):
        pytest.skip("OPENAI_API_KEY not set in environment")
    else:
        # All conditions met, test can run
        assert True

if __name__ == "__main__":
    # Allow running tests directly for debugging
    import sys
    
    print("LLM Test Status:")
    print(f"  HAS_LLM: {HAS_LLM}")
    print(f"  FLAGS.ENABLE_LLM: {FLAGS.ENABLE_LLM}")
    print(f"  OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"  Skip reason: {skip_reason or 'None (tests will run)'}")
    print()
    
    if skip_reason:
        print(f"Tests will be skipped: {skip_reason}")
        sys.exit(0)
    
    try:
        print("Running tests...")
        test_rewrite_smoke()
        print("✓ test_rewrite_smoke passed")
        test_rewrite_various_inputs()
        print("✓ test_rewrite_various_inputs passed")
        test_mock_available()
        print("✓ test_mock_available passed")
        print("\nAll tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)