# scripts/build_words_index.py  (real Zipf)
import sqlite3, re
from pathlib import Path
import cmudict
from wordfreq import zipf_frequency

ROOT = Path(__file__).resolve().parents[1]
DB   = ROOT / "data" / "dev" / "words_index.sqlite"

VOWELS = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
DIGITS = set("012")

def k_keys(phones):
    last = -1
    for i, p in enumerate(phones):
        if any(v in p for v in VOWELS) and any(d in p for d in "12"):
            last = i
    if last == -1:
        return "", "", ""
    tail = [re.sub(r"\d", "", t) for t in phones[last:]]
    k1   = re.sub(r"\d", "", phones[last])
    k2   = "-".join(tail[:2]) if tail else ""
    k3   = "-".join(tail)
    return k1, k2, k3

def stress_pattern(pron):
    digs = [c for c in pron if c.isdigit()]
    return "".join(digs) if digs else ""

def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS words;
    CREATE TABLE words(
      word   TEXT PRIMARY KEY,
      pron   TEXT NOT NULL,
      stress TEXT NOT NULL,
      syls   INTEGER NOT NULL,
      k1     TEXT NOT NULL,
      k2     TEXT NOT NULL,
      k3     TEXT NOT NULL,
      zipf   REAL
    );
    CREATE INDEX IF NOT EXISTS idx_words_k1   ON words(k1);
    CREATE INDEX IF NOT EXISTS idx_words_k2   ON words(k2);
    CREATE INDEX IF NOT EXISTS idx_words_k3   ON words(k3);
    CREATE INDEX IF NOT EXISTS idx_words_zipf ON words(zipf);
    """)
    d = cmudict.dict()
    rows = []
    for word, prons in d.items():
        phones = prons[0]
        k1, k2, k3 = k_keys(phones)
        stress = stress_pattern(" ".join(phones))
        syls = sum(1 for p in phones if any(v in p for v in VOWELS))
        # real Zipf (English)
        zipf = float(zipf_frequency(word, "en"))
        rows.append((word.lower(), " ".join(phones), stress, syls, k1, k2, k3, zipf))
    cur.executemany(
        "INSERT OR REPLACE INTO words(word,pron,stress,syls,k1,k2,k3,zipf) VALUES(?,?,?,?,?,?,?,?)",
        rows
    )
    con.commit()
    con.close()
    print(f"✅ built {DB} with {len(rows)} words (real Zipf)")
if __name__ == "__main__":
    main()
