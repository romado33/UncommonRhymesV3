"""
RhymeRarity - Anti-LLM Rhyme Engine
Advanced phonetic analysis and rare rhyme generation
"""

try:
    from .engine import search_rhymes, get_result_counts, organize_by_syllables
    from .phonetics import parse_pron, k_keys, extract_stress
except ImportError as e:
    print(f"Warning: Could not import rhyme_core modules: {e}")
    # Provide fallback None values
    search_rhymes = None
    get_result_counts = None
    organize_by_syllables = None

__version__ = "1.0.0"
__all__ = ['search_rhymes', 'get_result_counts', 'organize_by_syllables']
