"""
RhymeCore - Anti-LLM Rhyme Engine
Complete phonetic analysis and rhyme generation system
"""

from .engine import (
    search_rhymes,
    get_result_counts,
    organize_by_syllables,
    cfg,
    Config
)

__version__ = "1.0.0"
__all__ = [
    'search_rhymes',
    'get_result_counts', 
    'organize_by_syllables',
    'cfg',
    'Config'
]
