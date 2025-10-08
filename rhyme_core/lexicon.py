# rhyme_core/lexicon.py
from typing import Iterable

# Move import error handling to module level, not inside function
try:
    from rhyme_core.data import WORDLIST
except (ImportError, AttributeError):
    # Fallback: try to load from a file or use minimal set
    try:
        from pathlib import Path
        wordlist_path = Path(__file__).parent / "data" / "wordlist.txt"
        if wordlist_path.exists():
            WORDLIST = [line.strip() for line in wordlist_path.read_text().splitlines() if line.strip()]
        else:
            WORDLIST = []
    except Exception:
        WORDLIST = []

# Fallback minimal vocabulary if WORDLIST is empty
FALLBACK_VOCAB = [
    "double", "trouble", "stubble", "humble", "tumble", "bubble", "couple",
    "habit", "rabbit", "cabbage", "savage", "package", "damage", "manage",
    "paper", "vapor", "neighbor", "labor", "favor", "major", "danger",
    "simple", "sample", "example", "temple", "symbol", "tremble", "dimple",
    "people", "steeple", "feeble", "needle", "beetle", "beagle", "eagle"
]

def all_vocab_words() -> Iterable[str]:
    """
    Yield candidate words from your existing sources.
    Falls back to minimal set if no wordlist available.
    """
    if WORDLIST:
        for w in WORDLIST:
            if w:  # skip empty strings
                yield w
    else:
        # Use fallback vocabulary
        for w in FALLBACK_VOCAB:
            yield w