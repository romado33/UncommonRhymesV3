# rhyme_core/engine.py
"""
Simplified engine that uses pre-computed rhyme keys from the database.
The database already has k1, k2, k3 columns with rhyme keys computed!
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger('UncommonRhymes.Engine')

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "dev" / "words_index.sqlite"

@dataclass
class SearchConfig:
    relax_rap: bool = True
    include_rap: bool = False
    max_items: int = 20
    # separate rarity caps
    zipf_max_perfect: float = 4.0
    zipf_max_slant: float = 4.0
    zipf_max_multi: float = 5.5
    # slant level not used in this simplified version
    slant_level: str = "B"

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(str(DB_PATH))

def search(term: str, cfg: SearchConfig) -> Dict[str, List[Dict]]:
    """
    Search for rhymes using the database's pre-computed rhyme keys.
    
    The database has:
    - k1: nucleus rhyme key (for slant rhymes)
    - k2: nucleus + coda family (for better slant matching)
    - k3: full rhyme key (for perfect rhymes)
    """
    q = (term or "").strip().lower()
    if not q:
        return {
            "uncommon": [],
            "slant": [],
            "multiword": [],
            "rap_targets": [],
            "query_info": {}
        }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get query word data
        cursor.execute("SELECT word, pron, stress, syls, k1, k2, k3, zipf FROM words WHERE word = ?", (q,))
        query_row = cursor.fetchone()
        
        if not query_row:
            logger.warning(f"Query word '{q}' not found in database")
            return {
                "uncommon": [],
                "slant": [],
                "multiword": [],
                "rap_targets": [],
                "query_info": {}
            }
        
        query_word, query_pron, query_stress, query_syls, k1, k2, k3, query_zipf = query_row
        
        logger.info(f"Query '{q}': k1={k1}, k2={k2}, k3={k3}, zipf={query_zipf}")
        
        # Find perfect rhymes (matching k3)
        perfect_rhymes = []
        if k3:  # Only search if k3 is not empty
            cursor.execute("""
                SELECT word, pron, stress, syls, k1, k2, k3, zipf 
                FROM words 
                WHERE k3 = ? AND word != ? AND zipf <= ? AND zipf IS NOT NULL
                ORDER BY zipf ASC
                LIMIT ?
            """, (k3, q, cfg.zipf_max_perfect, cfg.max_items))
            
            for row in cursor.fetchall():
                word, pron, stress, syls, w_k1, w_k2, w_k3, zipf = row
                perfect_rhymes.append({
                    "word": word,
                    "syls": syls,
                    "stress": stress,
                    "zipf": zipf,
                    "why": f"Perfect rhyme (k3={k3}, zipf={zipf:.2f})"
                })
        
        # Find slant rhymes (matching k2 but not k3)
        slant_rhymes = []
        if k2:  # Only search if k2 is not empty
            cursor.execute("""
                SELECT word, pron, stress, syls, k1, k2, k3, zipf 
                FROM words 
                WHERE k2 = ? AND k3 != ? AND word != ? AND zipf <= ? AND zipf IS NOT NULL
                ORDER BY zipf ASC
                LIMIT ?
            """, (k2, k3 or '', q, cfg.zipf_max_slant, cfg.max_items))
            
            for row in cursor.fetchall():
                word, pron, stress, syls, w_k1, w_k2, w_k3, zipf = row
                slant_rhymes.append({
                    "word": word,
                    "syls": syls,
                    "stress": stress,
                    "zipf": zipf,
                    "why": f"Slant rhyme (k2={k2}, zipf={zipf:.2f})"
                })
        
        conn.close()
        
        logger.info(f"Found {len(perfect_rhymes)} perfect rhymes, {len(slant_rhymes)} slant rhymes")
        
        return {
            "uncommon": perfect_rhymes,
            "slant": slant_rhymes,
            "multiword": [],  # Not implemented yet
            "rap_targets": [],  # Not implemented yet
            "query_info": {
                "word": query_word,
                "syls": query_syls,
                "stress": query_stress,
                "meter": "",  # Can add meter logic later
            },
            "keys": {
                "k1": k1,
                "k2": k2,
                "k3": k3,
            },
            "focus_word": query_word
        }
        
    except Exception as e:
        logger.error(f"Search error for '{q}': {e}", exc_info=True)
        return {
            "uncommon": [],
            "slant": [],
            "multiword": [],
            "rap_targets": [],
            "query_info": {}
        }