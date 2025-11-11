import re
from typing import Optional, List, Tuple, Dict

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
    """Return (vowel_base, coda_tuple) taken from the LAST PRIMARY-STRESSED vowel; if none, last vowel."""
    # find indices of vowels and primary-stressed vowels
    vowel_idx = [i for i,p in enumerate(phones) if _is_vowel(p)]
    if not vowel_idx:
        return ("", tuple())
    
    # Only look for PRIMARY stress (marked with 1), not secondary stress (2)
    primary_stressed = [i for i,p in enumerate(phones) if _is_vowel(p) and p[-1] == "1"]
    
    # STRESS PATTERN CORRECTION: If multiple primary stresses, use the one that makes sense
    # For words like "stake-out" (EY1 K AW1 T), the second stress should be secondary
    if len(primary_stressed) > 1:
        # Use the first primary stress as the "real" primary stress
        # This handles cases where CMU marks both syllables as primary stress
        idx = primary_stressed[0]
    else:
        idx = primary_stressed[-1] if primary_stressed else vowel_idx[-1]
    
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
    - K2 match = Loose perfect (stress-agnostic) (0.85)
    - K2.5 match = Terminal match (compounds) (0.60)
    - K1 match = Assonance only (0.35)
    """
    # Get vowel base and coda from rhyme_tail
    v, c = rhyme_tail(phones)
    
    # Find the original primary-stressed vowel to get k3
    # (Same logic as rhyme_tail to ensure consistency)
    vowel_idx = [i for i, p in enumerate(phones) if _is_vowel(p)]
    if not vowel_idx:
        # Fallback if no vowels (shouldn't happen in real data)
        return (v, v, v)
    
    # Only look for PRIMARY stress (marked with 1), not secondary stress (2)
    primary_stressed = [i for i, p in enumerate(phones) if _is_vowel(p) and p[-1] == "1"]
    
    # STRESS PATTERN CORRECTION: If multiple primary stresses, use the one that makes sense
    if len(primary_stressed) > 1:
        # Use the first primary stress as the "real" primary stress
        idx = primary_stressed[0]
    else:
        idx = primary_stressed[-1] if primary_stressed else vowel_idx[-1]
    
    # Get the original vowel WITH stress marker
    v_stressed = phones[idx]
    
    # Build keys
    k1 = v  # Just vowel base: "AH"
    k2 = v + "|" + " ".join(c)  # Stress-agnostic: "AH|B AH0 L"
    k3 = v_stressed + "|" + " ".join(c)  # Stress-preserved: "AH1|B AH0 L"
    
    return (k1, k2, k3)

def coda(phones: List[str]) -> List[str]:
    return list(rhyme_tail(phones)[1])

def k0_upstream_assonance(phones1: List[str], phones2: List[str]) -> float:
    """
    K0: Upstream Assonance - Shared vowel classes before the rhyme tail.
    Returns score 0.10-0.25 based on overlap count/alignment.
    
    Example: guitar (G IH0 T AA1 R) vs designer (D IH0 Z AY1 N ER0)
    Both have IH upstream of their rhyme tails → K0 match
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Get rhyme tail positions for both words
    tail1_start = _find_rhyme_tail_start(phones1)
    tail2_start = _find_rhyme_tail_start(phones2)
    
    # Extract upstream vowels (before rhyme tail)
    upstream1 = [p for p in phones1[:tail1_start] if _is_vowel(p)]
    upstream2 = [p for p in phones2[:tail2_start] if _is_vowel(p)]
    
    if not upstream1 or not upstream2:
        return 0.0
    
    # Convert to vowel bases for comparison
    bases1 = [_vowel_base(v) for v in upstream1]
    bases2 = [_vowel_base(v) for v in upstream2]
    
    # Count matches
    matches = 0
    for base1 in bases1:
        if base1 in bases2:
            matches += 1
    
    # Calculate score based on overlap
    max_possible = min(len(bases1), len(bases2))
    if max_possible == 0:
        return 0.0
    
    overlap_ratio = matches / max_possible
    
    # Scale to 0.10-0.25 range
    return 0.10 + (overlap_ratio * 0.15)

def _find_rhyme_tail_start(phones: List[str]) -> int:
    """Find the index where the rhyme tail starts (last primary-stressed vowel)"""
    vowel_idx = [i for i, p in enumerate(phones) if _is_vowel(p)]
    if not vowel_idx:
        return len(phones)
    
    # Only look for PRIMARY stress (marked with 1), not secondary stress (2)
    primary_stressed = [i for i, p in enumerate(phones) if _is_vowel(p) and p[-1] == "1"]
    
    # STRESS PATTERN CORRECTION: If multiple primary stresses, use the one that makes sense
    if len(primary_stressed) > 1:
        # Use the first primary stress as the "real" primary stress
        idx = primary_stressed[0]
    else:
        idx = primary_stressed[-1] if primary_stressed else vowel_idx[-1]
    
    return idx

def kc_tail_consonance(phones1: List[str], phones2: List[str]) -> float:
    """
    KC: Tail Consonance - Coda consonant overlap with differing vowels.
    Weight by cluster length and order.
    
    Example: milk (M IH1 L K) vs walk (W AO1 K) → final K consonance
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Get rhyme tails
    _, coda1 = rhyme_tail(phones1)
    _, coda2 = rhyme_tail(phones2)
    
    # Extract consonants only from codas
    consonants1 = [p for p in coda1 if not _is_vowel(p)]
    consonants2 = [p for p in coda2 if not _is_vowel(p)]
    
    if not consonants1 or not consonants2:
        return 0.0
    
    # Check for consonant overlap (exact matches)
    matches = 0
    min_len = min(len(consonants1), len(consonants2))
    
    # Compare from the end (most important consonants)
    for i in range(min_len):
        if consonants1[-(i+1)] == consonants2[-(i+1)]:
            matches += 1
        else:
            break  # Stop at first mismatch
    
    if matches == 0:
        return 0.0
    
    # Weight by cluster length and order
    # Longer matches and matches closer to the end get higher scores
    max_possible = max(len(consonants1), len(consonants2))
    overlap_ratio = matches / max_possible
    
    # Scale to 0.0-1.0 range, with bonus for longer matches
    base_score = overlap_ratio
    length_bonus = min(0.2, matches * 0.05)  # Bonus for longer consonant clusters
    
    return min(1.0, base_score + length_bonus)

def kp_pararhyme(phones1: List[str], phones2: List[str]) -> float:
    """
    KP: Pararhyme - Onset+coda consonant frame match, vowel mismatch allowed.
    Penalize by vowel distance (feature space).
    
    Example: pad (P AE1 D) vs pod (P AA1 D) → P-D frame same, vowel differs
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Get rhyme tails
    _, coda1 = rhyme_tail(phones1)
    _, coda2 = rhyme_tail(phones2)
    
    # Extract onset (consonants before rhyme tail)
    tail_start1 = _find_rhyme_tail_start(phones1)
    tail_start2 = _find_rhyme_tail_start(phones2)
    
    onset1 = [p for p in phones1[:tail_start1] if not _is_vowel(p)]
    onset2 = [p for p in phones2[:tail_start2] if not _is_vowel(p)]
    
    # Extract coda consonants
    coda_consonants1 = [p for p in coda1 if not _is_vowel(p)]
    coda_consonants2 = [p for p in coda2 if not _is_vowel(p)]
    
    # Check onset+coda frame match
    onset_match = onset1 == onset2
    coda_match = coda_consonants1 == coda_consonants2
    
    if not (onset_match and coda_match):
        return 0.0
    
    # Get the rhyming vowels for distance calculation
    if tail_start1 < len(phones1) and tail_start2 < len(phones2):
        vowel1_base = _vowel_base(phones1[tail_start1])
        vowel2_base = _vowel_base(phones2[tail_start2])
    else:
        return 0.0
    
    if not vowel1_base or not vowel2_base:
        return 0.0
    
    # Calculate vowel distance penalty
    vowel_distance = _calculate_vowel_distance(vowel1_base, vowel2_base)
    
    # Base score for frame match, penalized by vowel distance
    base_score = 0.8  # High base score for frame match
    penalty = vowel_distance * 0.3  # Penalty based on vowel distance
    
    return max(0.0, base_score - penalty)

def _calculate_vowel_distance(vowel1: str, vowel2: str) -> float:
    """
    Calculate phonetic distance between two vowel bases.
    Returns 0.0 (identical) to 1.0 (very different).
    """
    if vowel1 == vowel2:
        return 0.0
    
    # Simple vowel feature mapping (height, backness, rounding)
    vowel_features = {
        # High vowels
        'IY': (3, 1, 0),  # high, front, unrounded
        'IH': (3, 1, 0),  # high, front, unrounded  
        'UW': (3, 3, 1),  # high, back, rounded
        'UH': (3, 3, 1),  # high, back, rounded
        
        # Mid vowels
        'EY': (2, 1, 0),  # mid, front, unrounded
        'EH': (2, 1, 0),  # mid, front, unrounded
        'OW': (2, 3, 1),  # mid, back, rounded
        'AO': (2, 3, 1),  # mid, back, rounded
        'ER': (2, 2, 0),  # mid, central, unrounded
        'AH': (2, 2, 0),  # mid, central, unrounded
        
        # Low vowels
        'AE': (1, 1, 0),  # low, front, unrounded
        'AA': (1, 3, 0),  # low, back, unrounded
        
        # Diphthongs
        'AW': (1.5, 2.5, 1),  # low-mid, back-central, rounded
        'AY': (1.5, 1.5, 0),  # low-mid, front-central, unrounded
        'OY': (2.5, 2, 1),    # mid-high, central-front, rounded
    }
    
    feat1 = vowel_features.get(vowel1, (2, 2, 0))
    feat2 = vowel_features.get(vowel2, (2, 2, 0))
    
    # Calculate Euclidean distance in feature space
    distance = ((feat1[0] - feat2[0])**2 + (feat1[1] - feat2[1])**2 + (feat1[2] - feat2[2])**2)**0.5
    
    # Normalize to 0-1 range (max possible distance is ~3.5)
    return min(1.0, distance / 3.5)

def calculate_phoneme_distance(phone1: str, phone2: str) -> float:
    """
    Calculate phonetic distance between any two phonemes (vowels or consonants).
    Returns 0.0 (identical) to 1.0 (very different).
    """
    if phone1 == phone2:
        return 0.0
    
    # Check if both are vowels
    if _is_vowel(phone1) and _is_vowel(phone2):
        base1 = _vowel_base(phone1)
        base2 = _vowel_base(phone2)
        return _calculate_vowel_distance(base1, base2)
    
    # Check if both are consonants
    elif not _is_vowel(phone1) and not _is_vowel(phone2):
        feat1 = _get_consonant_features(phone1)
        feat2 = _get_consonant_features(phone2)
        return _calculate_consonant_distance(feat1, feat2)
    
    # Mixed vowel/consonant - very different
    else:
        return 1.0

def _calculate_consonant_distance(feat1: Tuple[str, str, str], feat2: Tuple[str, str, str]) -> float:
    """
    Calculate distance between consonant feature tuples.
    Returns 0.0 (identical) to 1.0 (very different).
    """
    if feat1 == feat2:
        return 0.0
    
    # Feature weights: place=0.4, manner=0.4, voicing=0.2
    weights = [0.4, 0.4, 0.2]
    
    # Convert features to numeric values for distance calculation
    feature_map = {
        'place': {'bilabial': 1, 'labiodental': 2, 'dental': 3, 'alveolar': 4, 
                 'postalveolar': 5, 'palatal': 6, 'velar': 7, 'glottal': 8},
        'manner': {'stop': 1, 'fricative': 2, 'affricate': 3, 'nasal': 4, 
                   'liquid': 5, 'glide': 6},
        'voicing': {'voiceless': 0, 'voiced': 1}
    }
    
    distance = 0.0
    feature_keys = ['place', 'manner', 'voicing']
    
    for i, (f1, f2) in enumerate(zip(feat1, feat2)):
        if f1 != f2:
            # Get numeric values
            val1 = feature_map[feature_keys[i]].get(f1, 0)
            val2 = feature_map[feature_keys[i]].get(f2, 0)
            # Weighted distance
            max_val = len(feature_map[feature_keys[i]])
            distance += weights[i] * abs(val1 - val2) / max_val
    
    return min(1.0, distance)

def detect_internal_rhymes(phones: List[str]) -> List[Tuple[int, int, str, float]]:
    """
    Detect internal rhymes within a phrase.
    Returns list of (start_pos, end_pos, rhyme_type, score) tuples.
    
    Example: "I spray then I pray they pay today" → detects internal rhymes
    """
    if not phones:
        return []
    
    # Find all stressed vowels
    stressed_vowels = []
    for i, phone in enumerate(phones):
        if _is_vowel(phone) and phone[-1] in '12':  # Primary or secondary stress
            stressed_vowels.append((i, phone))
    
    if len(stressed_vowels) < 2:
        return []
    
    internal_rhymes = []
    
    # Check all pairs of stressed vowels
    for i in range(len(stressed_vowels)):
        for j in range(i + 1, len(stressed_vowels)):
            pos1, vowel1 = stressed_vowels[i]
            pos2, vowel2 = stressed_vowels[j]
            
            # Extract syllables around each stressed vowel
            syl1 = _extract_syllable_around(phones, pos1)
            syl2 = _extract_syllable_around(phones, pos2)
            
            if not syl1 or not syl2:
                continue
            
            # Check for different types of internal rhymes
            rhyme_type, score = _classify_internal_rhyme(syl1, syl2)
            
            if score > 0.3:  # Threshold for internal rhymes
                internal_rhymes.append((pos1, pos2, rhyme_type, score))
    
    # Sort by score (highest first)
    internal_rhymes.sort(key=lambda x: x[3], reverse=True)
    
    return internal_rhymes

def _extract_syllable_around(phones: List[str], vowel_pos: int) -> List[str]:
    """Extract syllable around a vowel position"""
    if vowel_pos < 0 or vowel_pos >= len(phones):
        return []
    
    # Find syllable boundaries
    start = vowel_pos
    end = vowel_pos + 1
    
    # Move backwards to find onset
    while start > 0 and not _is_vowel(phones[start - 1]):
        start -= 1
    
    # Move forwards to find coda
    while end < len(phones) and not _is_vowel(phones[end]):
        end += 1
    
    return phones[start:end]

def _classify_internal_rhyme(syl1: List[str], syl2: List[str]) -> Tuple[str, float]:
    """Classify internal rhyme type and score"""
    
    # Extract vowel bases
    vowel1 = None
    vowel2 = None
    
    for phone in syl1:
        if _is_vowel(phone):
            vowel1 = _vowel_base(phone)
            break
    
    for phone in syl2:
        if _is_vowel(phone):
            vowel2 = _vowel_base(phone)
            break
    
    if not vowel1 or not vowel2:
        return "none", 0.0
    
    # Check for perfect internal rhyme (same vowel)
    if vowel1 == vowel2:
        return "perfect", 1.0
    
    # Check for assonance (similar vowels)
    vowel_dist = _calculate_vowel_distance(vowel1, vowel2)
    if vowel_dist < 0.3:
        return "assonance", 0.7 - vowel_dist
    
    # Check for consonance (similar consonants)
    consonants1 = [p for p in syl1 if not _is_vowel(p)]
    consonants2 = [p for p in syl2 if not _is_vowel(p)]
    
    if consonants1 and consonants2:
        cons_dist = calculate_sequence_distance(consonants1, consonants2)
        if cons_dist < 0.4:
            return "consonance", 0.5 - cons_dist
    
    return "none", 0.0

def analyze_phrase_rhyme_density(phones: List[str]) -> Dict[str, float]:
    """
    Analyze rhyme density and patterns within a phrase.
    Returns metrics about internal rhyming.
    """
    if not phones:
        return {}
    
    internal_rhymes = detect_internal_rhymes(phones)
    
    # Count syllables
    vowel_count = sum(1 for p in phones if _is_vowel(p))
    
    # Count stressed syllables
    stressed_count = sum(1 for p in phones if _is_vowel(p) and p[-1] in '12')
    
    # Calculate metrics
    total_rhymes = len(internal_rhymes)
    rhyme_density = total_rhymes / max(1, stressed_count) if stressed_count > 0 else 0
    
    # Count by type
    perfect_count = sum(1 for _, _, rhyme_type, _ in internal_rhymes if rhyme_type == "perfect")
    assonance_count = sum(1 for _, _, rhyme_type, _ in internal_rhymes if rhyme_type == "assonance")
    consonance_count = sum(1 for _, _, rhyme_type, _ in internal_rhymes if rhyme_type == "consonance")
    
    return {
        'total_internal_rhymes': total_rhymes,
        'perfect_internal_rhymes': perfect_count,
        'assonance_internal_rhymes': assonance_count,
        'consonance_internal_rhymes': consonance_count,
        'rhyme_density': rhyme_density,
        'stressed_syllables': stressed_count,
        'total_syllables': vowel_count
    }

def calculate_sequence_distance(seq1: List[str], seq2: List[str]) -> float:
    """
    Calculate phonetic distance between two phoneme sequences using dynamic programming.
    Returns 0.0 (identical) to 1.0 (very different).
    """
    if not seq1 or not seq2:
        return 1.0 if seq1 or seq2 else 0.0
    
    # Dynamic programming approach (Levenshtein distance with phonetic costs)
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                # Calculate phonetic distance cost
                phoneme_cost = calculate_phoneme_distance(seq1[i-1], seq2[j-1])
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + phoneme_cost  # substitution with phonetic cost
                )
    
    # Normalize by sequence length
    max_len = max(m, n)
    return min(1.0, dp[m][n] / max_len)

def km_multisyllabic(phones1: List[str], phones2: List[str]) -> float:
    """
    KM: Multisyllabic Continuity - Consecutive syllable matches at K2 or stronger.
    Score scales with span length and stress alignment.
    
    Example: history (H IH1 S T ER0 IY0) vs mystery (M IH1 S T ER0 IY0) → 2-syllable match
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Find all vowels and their positions
    vowels1 = [(i, p) for i, p in enumerate(phones1) if _is_vowel(p)]
    vowels2 = [(i, p) for i, p in enumerate(phones2) if _is_vowel(p)]
    
    if len(vowels1) < 2 or len(vowels2) < 2:
        return 0.0  # Need at least 2 syllables for multisyllabic
    
    # Try to find the longest consecutive syllable match
    max_match_length = 0
    best_match_score = 0.0
    
    # Check all possible starting positions
    for start1 in range(len(vowels1)):
        for start2 in range(len(vowels2)):
            match_length = 0
            match_score = 0.0
            
            # Count consecutive matching syllables
            i, j = start1, start2
            while (i < len(vowels1) and j < len(vowels2) and 
                   i < len(phones1) and j < len(phones2)):
                
                # Get syllables (vowel + following consonants until next vowel)
                syl1 = _extract_syllable(phones1, vowels1[i][0])
                syl2 = _extract_syllable(phones2, vowels2[j][0])
                
                # Check if syllables match at K2 level (stress-agnostic)
                if _syllables_match_k2(syl1, syl2):
                    match_length += 1
                    # Bonus for stress alignment
                    stress_bonus = 0.1 if _stress_aligned(syl1, syl2) else 0.0
                    match_score += 1.0 + stress_bonus
                    i += 1
                    j += 1
                else:
                    break
            
            # Update best match
            if match_length > max_match_length:
                max_match_length = match_length
                best_match_score = match_score
    
    if max_match_length < 2:
        return 0.0  # Need at least 2 syllables for multisyllabic
    
    # Scale score: longer matches get higher scores
    base_score = best_match_score / max_match_length
    length_bonus = min(0.3, (max_match_length - 2) * 0.1)  # Bonus for 3+ syllables
    
    return min(1.0, base_score + length_bonus)

def _extract_syllable(phones: List[str], vowel_pos: int) -> List[str]:
    """Extract a syllable starting from the vowel at vowel_pos"""
    if vowel_pos >= len(phones):
        return []
    
    syllable = []
    i = vowel_pos
    
    # Add the vowel
    syllable.append(phones[i])
    i += 1
    
    # Add consonants until next vowel or end
    while i < len(phones) and not _is_vowel(phones[i]):
        syllable.append(phones[i])
        i += 1
    
    return syllable

def _syllables_match_k2(syl1: List[str], syl2: List[str]) -> bool:
    """Check if two syllables match at K2 level (stress-agnostic)"""
    if len(syl1) != len(syl2):
        return False
    
    for p1, p2 in zip(syl1, syl2):
        if _is_vowel(p1) and _is_vowel(p2):
            # Compare vowel bases (ignore stress)
            if _vowel_base(p1) != _vowel_base(p2):
                return False
        else:
            # Compare consonants exactly
            if p1 != p2:
                return False
    
    return True

def _stress_aligned(syl1: List[str], syl2: List[str]) -> bool:
    """Check if syllables have aligned stress patterns"""
    vowels1 = [p for p in syl1 if _is_vowel(p)]
    vowels2 = [p for p in syl2 if _is_vowel(p)]
    
    if not vowels1 or not vowels2:
        return False
    
    # Check if both have same stress level
    stress1 = vowels1[0][-1] if vowels1[0][-1].isdigit() else '0'
    stress2 = vowels2[0][-1] if vowels2[0][-1].isdigit() else '0'
    
    return stress1 == stress2

def kf_family_rhymes(phones1: List[str], phones2: List[str]) -> float:
    """
    KF: Family Rhymes - Consonant equivalence by place/manner/voicing.
    Replace consonants with feature classes and compute equivalence overlap.
    
    Example: dad (D AE1 D) vs bad (B AE1 D) → both alveolar stops
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Get rhyme tails
    _, coda1 = rhyme_tail(phones1)
    _, coda2 = rhyme_tail(phones2)
    
    # Extract consonants from codas
    consonants1 = [p for p in coda1 if not _is_vowel(p)]
    consonants2 = [p for p in coda2 if not _is_vowel(p)]
    
    if not consonants1 or not consonants2:
        return 0.0
    
    # Convert consonants to feature vectors
    features1 = [_get_consonant_features(c) for c in consonants1]
    features2 = [_get_consonant_features(c) for c in consonants2]
    
    # Calculate feature overlap
    matches = 0
    min_len = min(len(features1), len(features2))
    
    # Compare from the end (most important consonants)
    for i in range(min_len):
        if _features_equivalent(features1[-(i+1)], features2[-(i+1)]):
            matches += 1
        else:
            break  # Stop at first mismatch
    
    if matches == 0:
        return 0.0
    
    # Weight by family similarity
    max_possible = max(len(features1), len(features2))
    overlap_ratio = matches / max_possible
    
    # Bonus for family matches (not exact matches)
    family_bonus = 0.0
    for i in range(matches):
        if features1[-(i+1)] != features2[-(i+1)]:  # Not exact match
            family_bonus += 0.1
    
    return min(1.0, overlap_ratio + family_bonus)

def _get_consonant_features(consonant: str) -> Tuple[str, str, str]:
    """
    Get consonant features: (place, manner, voicing)
    Returns feature tuple for comparison
    """
    # Consonant feature mapping based on ARPABET
    consonant_features = {
        # Stops
        'P': ('bilabial', 'stop', 'voiceless'),
        'B': ('bilabial', 'stop', 'voiced'),
        'T': ('alveolar', 'stop', 'voiceless'),
        'D': ('alveolar', 'stop', 'voiced'),
        'K': ('velar', 'stop', 'voiceless'),
        'G': ('velar', 'stop', 'voiced'),
        
        # Fricatives
        'F': ('labiodental', 'fricative', 'voiceless'),
        'V': ('labiodental', 'fricative', 'voiced'),
        'TH': ('dental', 'fricative', 'voiceless'),
        'DH': ('dental', 'fricative', 'voiced'),
        'S': ('alveolar', 'fricative', 'voiceless'),
        'Z': ('alveolar', 'fricative', 'voiced'),
        'SH': ('postalveolar', 'fricative', 'voiceless'),
        'ZH': ('postalveolar', 'fricative', 'voiced'),
        'HH': ('glottal', 'fricative', 'voiceless'),
        
        # Affricates
        'CH': ('postalveolar', 'affricate', 'voiceless'),
        'JH': ('postalveolar', 'affricate', 'voiced'),
        
        # Nasals
        'M': ('bilabial', 'nasal', 'voiced'),
        'N': ('alveolar', 'nasal', 'voiced'),
        'NG': ('velar', 'nasal', 'voiced'),
        
        # Liquids
        'L': ('alveolar', 'liquid', 'voiced'),
        'R': ('alveolar', 'liquid', 'voiced'),
        
        # Glides
        'W': ('bilabial', 'glide', 'voiced'),
        'Y': ('palatal', 'glide', 'voiced'),
    }
    
    return consonant_features.get(consonant, ('unknown', 'unknown', 'unknown'))

def _features_equivalent(feat1: Tuple[str, str, str], feat2: Tuple[str, str, str]) -> bool:
    """
    Check if two consonant feature tuples are equivalent.
    Allows family matches (same place/manner) even if voicing differs.
    """
    if feat1 == feat2:
        return True  # Exact match
    
    # Family match: same place and manner, voicing can differ
    if feat1[0] == feat2[0] and feat1[1] == feat2[1]:
        return True
    
    # Special cases for similar places
    place_equivalents = {
        'alveolar': ['postalveolar'],
        'postalveolar': ['alveolar'],
        'dental': ['alveolar'],
        'alveolar': ['dental'],
    }
    
    if (feat1[0] in place_equivalents.get(feat2[0], []) and 
        feat1[1] == feat2[1]):
        return True
    
    return False

def kr_rarity_index(phones: List[str], zipf_freq: float = 5.0) -> float:
    """
    KR: Rarity Index - Rarity of the rhyme tail class.
    Higher when rhyme tail is rare (1 is rarest, 0 is most common).
    
    Uses Zipf frequency as a proxy for rarity since we don't have corpus data.
    """
    if not phones:
        return 0.0
    
    # Get rhyme tail
    vowel_base, coda = rhyme_tail(phones)
    
    # Create tail class (vowel_base + coda_no_stress)
    tail_class = vowel_base + "|" + " ".join(coda)
    
    # Use Zipf frequency as rarity proxy
    # Higher Zipf = more common = lower rarity score
    # Lower Zipf = less common = higher rarity score
    
    # Convert Zipf to rarity (0-1 scale)
    # Zipf 7+ = very common (rarity 0.0-0.2)
    # Zipf 4-6 = common (rarity 0.2-0.5)  
    # Zipf 2-3 = uncommon (rarity 0.5-0.8)
    # Zipf 0-1 = rare (rarity 0.8-1.0)
    
    if zipf_freq >= 7.0:
        rarity = 0.0 + (7.0 - zipf_freq) * 0.1  # 0.0-0.2
    elif zipf_freq >= 4.0:
        rarity = 0.2 + (4.0 - zipf_freq) * 0.1  # 0.2-0.5
    elif zipf_freq >= 2.0:
        rarity = 0.5 + (2.0 - zipf_freq) * 0.15  # 0.5-0.8
    else:
        rarity = 0.8 + (2.0 - zipf_freq) * 0.1  # 0.8-1.0
    
    return max(0.0, min(1.0, rarity))

def calculate_wrs(phones1: List[str], phones2: List[str], zipf1: float = 5.0, zipf2: float = 5.0) -> float:
    """
    WRS: Weighted Rhyme Score - Complete scoring formula from spec.
    
    WRS = 1.00*S_K3 + 0.85*(1-S_K3)*S_K2 + 0.60*(1-S_K3)*(1-S_K2)*S_K2_5 + 
          0.35*(1-S_K3)*(1-S_K2)*(1-S_K2_5)*S_K1 + 0.20*S_KC + 0.15*S_KF + 
          0.15*S_KP + 0.10*min(S_KM, 1.0) + S_K0 + 0.20*KR
    
    Returns score 0.0-1.0
    """
    if not phones1 or not phones2:
        return 0.0
    
    # Calculate all K-key scores
    k1_1, k2_1, k3_1 = k_keys(phones1)
    k1_2, k2_2, k3_2 = k_keys(phones2)
    
    # Core K-keys (binary)
    s_k3 = 1.0 if k3_1 == k3_2 else 0.0
    s_k2 = 1.0 if k2_1 == k2_2 else 0.0
    s_k2_5 = 1.0 if terminal_match(phones1, phones2) else 0.0
    s_k1 = 1.0 if k1_1 == k1_2 else 0.0
    
    # Extended K-keys (continuous)
    s_kc = kc_tail_consonance(phones1, phones2)
    s_kf = kf_family_rhymes(phones1, phones2)
    s_kp = kp_pararhyme(phones1, phones2)
    s_km = km_multisyllabic(phones1, phones2)
    s_k0 = k0_upstream_assonance(phones1, phones2)
    
    # Rarity (average of both words)
    zipf1 = zipf1 or 5.0  # Default to common word if None
    zipf2 = zipf2 or 5.0  # Default to common word if None
    kr1 = kr_rarity_index(phones1, zipf1)
    kr2 = kr_rarity_index(phones2, zipf2)
    kr = (kr1 + kr2) / 2.0
    
    # Calculate WRS using the spec formula
    wrs = (
        1.00 * s_k3 +
        0.85 * (1 - s_k3) * s_k2 +
        0.60 * (1 - s_k3) * (1 - s_k2) * s_k2_5 +
        0.35 * (1 - s_k3) * (1 - s_k2) * (1 - s_k2_5) * s_k1 +
        0.20 * s_kc +
        0.15 * s_kf +
        0.15 * s_kp +
        0.10 * min(s_km, 1.0) +
        s_k0 +
        0.20 * kr
    )
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, wrs))

def terminal_match(phones1: List[str], phones2: List[str]) -> bool:
    """
    Check if two words have matching final syllable rime (terminal match).
    Useful for compounds like "stakeout" vs "without" where final syllable matches
    but primary stress is earlier.
    """
    if not phones1 or not phones2:
        return False
    
    # Get the last syllable of each word
    last_syl1 = phones1[-1] if phones1 else ""
    last_syl2 = phones2[-1] if phones2 else ""
    
    # For multi-syllable words, get the last vowel + coda
    # Find last vowel in each word
    vowels1 = [i for i, p in enumerate(phones1) if _is_vowel(p)]
    vowels2 = [i for i, p in enumerate(phones2) if _is_vowel(p)]
    
    if not vowels1 or not vowels2:
        return False
    
    # Get last vowel + everything after it
    last_vowel_idx1 = vowels1[-1]
    last_vowel_idx2 = vowels2[-1]
    
    terminal1 = phones1[last_vowel_idx1:]
    terminal2 = phones2[last_vowel_idx2:]
    
    # Check if terminal syllables match (ignoring stress)
    if len(terminal1) != len(terminal2):
        return False
    
    for p1, p2 in zip(terminal1, terminal2):
        # Compare vowel bases and consonants, ignoring stress
        base1 = _vowel_base(p1) if _is_vowel(p1) else p1
        base2 = _vowel_base(p2) if _is_vowel(p2) else p2
        if base1 != base2:
            return False
    
    return True

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