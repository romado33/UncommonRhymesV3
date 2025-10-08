import sqlite3
from typing import Dict, Any, List, Tuple
from .data.paths import rap_db, words_db

def _con(path):
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    return con

def find_rap_targets(query_k1: str, query_k2: str, min_needed=10, max_show=20, relax=True) -> Tuple[List[Dict[str,Any]], int]:
    rdb = rap_db()
    if not rdb:
        return [], 0
    con = _con(rdb)
    con_w = _con(words_db())

    # strict: all rows whose target_word has k2==query_k2
    strict_words = {r["word"] for r in con_w.execute("SELECT word FROM words WHERE k2=?", (query_k2,)).fetchall()}
    
    rows = []
    if strict_words:
        # Fixed: proper parameterized query without string formatting
        placeholders = ",".join("?" * len(strict_words))
        sql = f"SELECT * FROM song_rhyme_patterns WHERE LOWER(target_word) IN ({placeholders})"
        rows = [dict(r) | {"relax_level": 1.0}
                for r in con.execute(sql, tuple(w.lower() for w in strict_words)).fetchall()]

    if relax and len(rows) < min_needed:
        k1_words = {r["word"] for r in con_w.execute("SELECT word FROM words WHERE k1=?", (query_k1,)).fetchall()}
        
        if k1_words:
            # Fixed: proper parameterized query without string formatting
            placeholders = ",".join("?" * len(k1_words))
            sql = f"SELECT * FROM song_rhyme_patterns WHERE LOWER(target_word) IN ({placeholders})"
            rows += [dict(r) | {"relax_level": 2.0}
                     for r in con.execute(sql, tuple(w.lower() for w in k1_words)).fetchall()]

    rows.sort(key=lambda r: (-(r.get("phonetic_similarity") or 0), 
                              -(r.get("confidence_score") or 0), 
                              -(r.get("rhyme_density") or 0), 
                              r.get("relax_level", 9)))
    total = len(rows)
    return rows[:max_show], total