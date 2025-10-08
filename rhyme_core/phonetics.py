import re
from typing import Optional, List, Tuple

VOWELS = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
VOWEL_RE = re.compile(r"^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)[0-2]?$")

def parse_pron(pron_str: str) -> List[str]:
    return [p.strip() for p in pron_str.split() if p.strip()]

def _is_vowel(phone: str) -> bool:
    m = VOWEL_RE.match(phone)
    return bool(m)

def _vowel_base(phone: str) -> Optional[str]:
    m = VOWEL_RE.match(phone)
    return m.group(1) if m else None

def rhyme_tail(phones: List[str]) -> Tuple[str, Tuple[str, ...]]:
    """Return (vowel_base, coda_tuple) taken from the LAST STRESSED vowel; if none, last vowel."""
    # find indices of vowels and stressed vowels
    vowel_idx = [i for i,p in enumerate(phones) if _is_vowel(p)]
    if not vowel_idx:
        return ("", tuple())
    stressed = [i for i,p in enumerate(phones) if _is_vowel(p) and p[-1] in "12"]
    idx = stressed[-1] if stressed else vowel_idx[-1]
    v = _vowel_base(phones[idx]) or ""
    coda = tuple(phones[idx+1:])
    return (v, coda)

def k_keys(phones: List[str]) -> Tuple[str, str, str]:
    """k1 = vowel_base, k2 = vowel_base|coda, k3 unused for now."""
    v, c = rhyme_tail(phones)
    k1 = v
    k2 = v + "|" + " ".join(c)
    k3 = ""
    return (k1, k2, k3)

def coda(phones: List[str]) -> List[str]:
    return list(rhyme_tail(phones)[1])

def meter_name(stress_pattern: str) -> str:
    # trivial mapper; keep as before if you already had one
    if not stress_pattern:
        return "unknown"
    if stress_pattern.endswith("01") or stress_pattern=="01":
        return "iamb"
    if stress_pattern.endswith("10") or stress_pattern=="10":
        return "trochee"
    if stress_pattern.endswith("010"):
        return "amphibrach"
    if stress_pattern.endswith("100"):
        return "dactyl"
    if stress_pattern.endswith("001"):
        return "anapest"
    return "mixed"


# --- utilities for slant ranking ---
def _levenshtein_tokens(a: List[str], b: List[str]) -> int:
    """Edit distance on token lists (insert/delete/substitute = 1)."""
    n, m = len(a), len(b)
    if n == 0: return m
    if m == 0: return n
    dp = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0] = i
    for j in range(m+1): dp[0][j] = j
    for i in range(1, n+1):
        ai = a[i-1]
        for j in range(1, m+1):
            cost = 0 if ai == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost  # substitution
            )
    return dp[n][m]

def tail_distance(q_tail_phones: List[str], cand_phones: List[str]) -> int:
    """
    Distance between the query tail phones and the candidate's tail phones.
    Lower is better; 0 means identical coda after the last stressed vowel.
    """
    return _levenshtein_tokens(list(q_tail_phones), coda(cand_phones))