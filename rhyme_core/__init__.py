"""
RhymeRarity - Anti-LLM Rhyme Engine
Advanced phonetic analysis and rare rhyme generation
"""

try:
    from .search import search_all_categories, search_rhymes
    from .phonetics import parse_pron, k_keys, extract_stress
except ImportError as e:
    print(f"Warning: Could not import rhyme_core modules: {e}")
    # Provide fallback None values
    search_all_categories = None
    search_rhymes = None

__version__ = "1.0.0"
__all__ = ['search_all_categories', 'search_rhymes']
