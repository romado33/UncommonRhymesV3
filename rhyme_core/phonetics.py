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
    """
    Generate rhyme keys with proper stress handling.
    
    k1 = vowel_base only (e.g., "AH")
    k2 = vowel_base|coda with stress stripped from nucleus (e.g., "AH|B AH0 L")
    k3 = vowel_with_stress|coda with stress preserved (e.g., "AH1|B AH0 L")
    
    Examples for "double" /D AH1 B AH0 L/:
    - k1 = "AH"              (just vowel base)
    - k2 = "AH|B AH0 L"      (stress-agnostic nucleus, matches "trouble" regardless of stress)
    - k3 = "AH1|B AH0 L"     (stress-preserved nucleus, only matches same stress pattern)
    
    Rhyme strength hierarchy:
    - K3 match = Strict perfect rhyme (1.00)
    - K2 match = Perfect by ear (0.85)
    - K1 match = Assonance only (0.35)
    """
    # Get vowel base and coda from rhyme_tail
    v, c = rhyme_tail(phones)
    
    # Find the original stressed vowel to get k3
    # (Same logic as rhyme_tail to ensure consistency)
    vowel_idx = [i for i, p in enumerate(phones) if _is_vowel(p)]
    if not vowel_idx:
        # Fallback if no vowels (shouldn't happen in real data)
        return (v, v, v)
    
    stressed = [i for i, p in enumerate(phones) if _is_vowel(p) and p[-1] in "12"]
    idx = stressed[-1] if stressed else vowel_idx[-1]
    
    # Get the original vowel WITH stress marker
    v_stressed = phones[idx]
    
    # Build keys
    k1 = v  # Just vowel base: "AH"
    k2 = v + "|" + " ".join(c)  # Stress-agnostic: "AH|B AH0 L"
    k3 = v_stressed + "|" + " ".join(c)  # Stress-preserved: "AH1|B AH0 L"
    
    return (k1, k2, k3)

def coda(phones: List[str]) -> List[str]:
    return list(rhyme_tail(phones)[1])

# =============================================================================
# MISSING FUNCTIONS - Added for diagnostic_tests.py compatibility
# =============================================================================

def extract_stress_pattern(phones: List[str]) -> str:
    """
    Extract stress pattern from phoneme list.
    
    Args:
        phones: List of phonemes (e.g., ['D', 'AA1', 'B', 'AH0', 'L'])
    
    Returns:
        Stress pattern string (e.g., '1-0' for double)
    
    Examples:
        ['D', 'AA1', 'L', 'ER0'] -> '1-0'
        ['K', 'AE1', 'T'] -> '1'
        ['S', 'IH0', 'L', 'AE1', 'B', 'AH0', 'L'] -> '0-1-0'
    """
    stress_marks = []
    for phone in phones:
        if _is_vowel(phone):
            # Extract stress digit (0, 1, or 2)
            if phone[-1] in '012':
                stress_marks.append(phone[-1])
            else:
                stress_marks.append('0')  # Default to unstressed
    
    return '-'.join(stress_marks)

def extract_stress(phones: List[str]) -> str:
    """
    Alias for extract_stress_pattern for backward compatibility.
    
    This is the function that diagnostic_tests.py imports.
    """
    return extract_stress_pattern(phones)

def strip_stress(phone: str) -> str:
    """
    Remove stress marker from a phoneme.
    
    Args:
        phone: Phoneme with optional stress (e.g., 'AA1', 'B', 'AH0')
    
    Returns:
        Phoneme without stress marker (e.g., 'AA', 'B', 'AH')
    
    Examples:
        strip_stress('AA1') -> 'AA'
        strip_stress('B') -> 'B'
        strip_stress('AH0') -> 'AH'
    """
    if phone and phone[-1] in '012':
        return phone[:-1]
    return phone

def is_vowel(phone: str) -> bool:
    """
    Public wrapper for _is_vowel for external use.
    
    Args:
        phone: Phoneme to check (e.g., 'AA1', 'B', 'AH0')
    
    Returns:
        True if phone is a vowel, False otherwise
    """
    return _is_vowel(phone)

def meter_name(stress_pattern: str) -> str:
    """
    Map stress pattern to poetic meter name.
    
    Args:
        stress_pattern: Stress pattern string (e.g., '1-0', '0-1')
    
    Returns:
        Meter name (e.g., 'trochee', 'iamb', 'mixed')
    """
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