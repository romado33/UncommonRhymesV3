"""
RhymeRarity Data Package
Database paths and configuration
"""

try:
    from .paths import words_db, get_db_path
except ImportError:
    words_db = None
    get_db_path = None

__all__ = ['words_db', 'get_db_path']
