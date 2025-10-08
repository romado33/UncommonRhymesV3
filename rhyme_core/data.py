# rhyme_core/data.py
"""
Data providers for CMU pronunciations and Zipf frequencies.
Reads from the SQLite database.
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('UncommonRhymes.Data')

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "dev" / "words_index.sqlite"

# Lazy-loaded caches
_CMU_DICT: Optional[Dict[str, List[str]]] = None
_ZIPF_MAP: Optional[Dict[str, float]] = None
_WORDLIST: Optional[List[str]] = None

def _load_from_db():
    """Load CMU and ZIPF data from database into memory."""
    global _CMU_DICT, _ZIPF_MAP, _WORDLIST
    
    if _CMU_DICT is not None and _ZIPF_MAP is not None and _WORDLIST is not None:
        return  # Already loaded
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        _CMU_DICT = {}
        _ZIPF_MAP = {}
        _WORDLIST = []
        
        logger.info("Loading pronunciation and frequency data from database...")
        cursor.execute("SELECT word, pron, zipf FROM words ORDER BY word")
        
        for row in cursor:
            word, pron, zipf = row
            word_lower = word.lower()
            
            # Add to wordlist
            _WORDLIST.append(word)
            
            # Parse pronunciation (stored as space-separated phones)
            phones = pron.split()
            _CMU_DICT[word_lower] = [phones]  # Wrap in list for multiple pronunciations
            
            # Store zipf score
            if zipf is not None:
                _ZIPF_MAP[word_lower] = float(zipf)
        
        conn.close()
        logger.info(f"Loaded {len(_WORDLIST):,} words, {len(_CMU_DICT):,} pronunciations, and {len(_ZIPF_MAP):,} frequency scores")
        
    except Exception as e:
        logger.error(f"Error loading data from database: {e}")
        _CMU_DICT = {}
        _ZIPF_MAP = {}
        _WORDLIST = []

# Initialize on import
try:
    _load_from_db()
except Exception as e:
    logger.error(f"Failed to initialize data module: {e}")
    _CMU_DICT = {}
    _ZIPF_MAP = {}
    _WORDLIST = []

# Module-level exports (what engine.py and lexicon.py expect)
# These need to be actual variables, not functions
CMU_DICT = _CMU_DICT if _CMU_DICT is not None else {}
ZIPF_MAP = _ZIPF_MAP if _ZIPF_MAP is not None else {}
WORDLIST = _WORDLIST if _WORDLIST is not None else []