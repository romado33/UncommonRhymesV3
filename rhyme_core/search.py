from pathlib import Path
import sqlite3, os
from .data.paths import words_db, rap_db
from .phonetics import k_keys

UNCOMMON_ZIPF_MAX = float(os.getenv(""UR_UNCOMMON_ZIPF_MAX"", ""4.0""))

def _con(db_path: Path):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con

def _words_for_key(k2: str, limit: int = 200):
    con = _con(words_db())
    cur = con.execute(""SELECT word, pron, zipf FROM words WHERE k2=? ORDER BY zipf ASC LIMIT ?"", (k2, limit))
    return [dict(r) | {""why"": f""strict rhyme (k2={k2})""} for r in cur.fetchall()]

def _words_for_k1(k1: str, limit: int = 300):
    con = _con(words_db())
    cur = con.execute(""SELECT word, pron, zipf FROM words WHERE k1=? ORDER BY zipf ASC LIMIT ?"", (k1, limit))
    return [dict(r) | {""why"": f""assonance (k1={k1})""} for r in cur.fetchall()]

def _filter_uncommon(rows, max_zipf=UNCOMMON_ZIPF_MAX):
    return [r for r in rows if r.get(""zipf"", 9) <= max_zipf]

def _phones(word: str):
    # naive: look up pron in words table
    con = _con(words_db())
    r = con.execute(""SELECT pron FROM words WHERE word=? LIMIT 1"", (word.lower(),)).fetchone()
    return r[""pron""].split() if r else []

def search_all_categories(term: str, max_items=20, relax_rap=True):
    ph = _phones(term)
    k1, k2, k3 = k_keys(ph)

    # Uncommon (strict rhyme â†’ then assonance if short)
    unc = _filter_uncommon(_words_for_key(k2, 400))
    if len(unc) < 10:
        unc += _filter_uncommon(_words_for_k1(k1, 400))
    uncommon = unc[:max_items]

    # Slant (just use k1 pool minus strict dupes)
    slant_pool = _words_for_k1(k1, 400)
    seen = {r[""word""] for r in unc}
    slant = [r for r in slant_pool if r[""word""] not in seen][:max_items]

    # Multiword (placeholder: reuse strict k2 for now)
    multi = _words_for_key(k2, 400)[:max_items]

    # Rap targets
    rap_rows, rap_total = [], 0
    rdb = rap_db()
    if rdb:
        con = sqlite3.connect(str(rdb)); con.row_factory = sqlite3.Row
        # strict target k2 (join via words table to compute k2)
        q = """
        SELECT s.*, 1.0 as relax_level FROM song_rhyme_patterns s
        WHERE LOWER(target_word) IN (
          SELECT word FROM words WHERE k2 = ?
        )
        """
        rap_rows = [dict(r) for r in con.execute(q, (k2,)).fetchall()]
        if relax_rap and len(rap_rows) < 10:
            q2 = """
            SELECT s.*, 2.0 as relax_level FROM song_rhyme_patterns s
            WHERE LOWER(target_word) IN (
              SELECT word FROM words WHERE k1 = ?
            )
            """
            rap_rows += [dict(r) for r in con.execute(q2, (k1,)).fetchall()]
        rap_rows = sorted(rap_rows, key=lambda r: (-float(r.get(""phonetic_similarity"",0) or 0),
                                                   -float(r.get(""confidence_score"",0) or 0),
                                                   -float(r.get(""rhyme_density"",0) or 0),
                                                    r.get(""relax_level"", 3.0)))
        rap_total = len(rap_rows)
    rap_targets = rap_rows[:max_items]

    return {
      ""uncommon"": uncommon,
      ""slant"": slant,
      ""multiword"": multi,
      ""rap_targets"": rap_targets,
      ""uncommon_total"": len(unc),
      ""slant_total"": len(slant_pool),
      ""multiword_total"": 400,  # placeholder
      ""rap_targets_total"": rap_total
    }
