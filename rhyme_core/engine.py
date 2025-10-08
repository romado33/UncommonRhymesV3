# rhyme_core/engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Iterable, Optional
import re
import math

# ---- external helpers already in your repo ----
# parse_pron(term) -> List[List[str]]   # list of possible ARPAbet seqs
# zipf_freq(word)  -> float | None      # word frequency (Zipf), lower = rarer
# cmu_word_phones(word: str) -> List[List[str]] | []  # direct CMU lookup

# ---- ADDED: missing function definitions ----
def cmu_word_phones(word: str) -> List[List[str]]:
    """
    Return CMU pronunciations for word.
    This is a placeholder - wire to your actual CMU dict.
    """
    try:
        # Try to import from your data module
        from rhyme_core.data import CMU_DICT
        w = word.lower()
        pron = CMU_DICT.get(w, [])
        # CMU dict might store as space-separated string or list
        if isinstance(pron, str):
            return [[p.strip() for p in pron.split()]]
        elif isinstance(pron, list) and pron and isinstance(pron[0], str):
            return [pron]
        return pron if pron else []
    except (ImportError, AttributeError):
        # Fallback: empty result
        return []

def zipf_freq(word: str) -> Optional[float]:
    """
    Return Zipf frequency score for word (higher = more common).
    This is a placeholder - wire to your actual frequency data.
    """
    try:
        # Try to import from your data module
        from rhyme_core.data import ZIPF_MAP
        return ZIPF_MAP.get(word.lower())
    except (ImportError, AttributeError):
        # Fallback: treat as moderately rare
        return 3.5

try:
    from rhyme_core.providers import datamuse as dm  # our thin wrapper you added
except Exception:  # harden if provider not present
    dm = None

VOWELS = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}
VOWEL_RE = re.compile(r"^(?P<base>[A-Z]{2})(?P<stress>[012])?$")  # e.g., AH0

# --------------------------- config ---------------------------

@dataclass
class SearchConfig:
    relax_rap: bool = True
    include_rap: bool = False
    max_items: int = 20
    # separate rarity caps
    zipf_max_perfect: float = 4.0
    zipf_max_slant: float = 4.0
    zipf_max_multi: float = 5.5
    # slant level: "A" nucleus only, "B" = nucleus + coda family, "C" = coda family only
    slant_level: str = "B"

# ---------------------- phonetic utilities ----------------------

def is_vowel(ph: str) -> bool:
    m = VOWEL_RE.match(ph)
    return bool(m and m.group("base") in VOWELS)

def phone_base(ph: str) -> str:
    m = VOWEL_RE.match(ph)
    if not m: return ph
    return m.group("base")

def phone_stress(ph: str) -> Optional[int]:
    m = VOWEL_RE.match(ph)
    if not m: return None
    s = m.group("stress")
    return None if s is None else int(s)

def split_syllables(phones: List[str]) -> List[List[str]]:
    """
    Very standard CMU syllabifier: each vowel starts a new syllable.
    """
    syls: List[List[str]] = []
    cur: List[str] = []
    for ph in phones:
        if is_vowel(ph):
            if cur:
                syls.append(cur)
            cur = [ph]
        else:
            cur.append(ph)
    if cur:
        syls.append(cur)
    return syls

def last_stressed_nucleus(phones: List[str]) -> Tuple[str, int]:
    """
    Returns (vowel_base, stress) for the last vowel. If none, ('', -1)
    """
    last = ("", -1)
    for ph in phones:
        if is_vowel(ph):
            last = (phone_base(ph), phone_stress(ph) or 0)
    return last

def coda_of_last_syllable(phones: List[str]) -> Tuple[str, ...]:
    syls = split_syllables(phones)
    if not syls:
        return tuple()
    last = syls[-1]
    # remove vowel nucleus & any trailing vowel-like schwas (rare in CMU tails)
    tail: List[str] = []
    seen_vowel = False
    for ph in last:
        if is_vowel(ph):
            seen_vowel = True
            continue
        if seen_vowel:
            tail.append(ph)
    # normalize trivial variants
    return normalize_coda(tuple(tail))

# map many tails into consonant-family buckets for slant-B/C
CODA_FAMILY = {
    "T":"STOP_ALV", "D":"STOP_ALV",
    "K":"STOP_VEL", "G":"STOP_VEL",
    "P":"STOP_BIL", "B":"STOP_BIL",
    "S":"SIBIL", "Z":"SIBIL", "SH":"SIBIL", "ZH":"SIBIL",
    "F":"FRIC", "V":"FRIC", "TH":"FRIC", "DH":"FRIC",
    "M":"NAS", "N":"NAS", "NG":"NAS",
    "L":"LIQ", "R":"LIQ", "ER":"LIQ",  # r-colored treated liquid-ish
    "CH":"AFF", "JH":"AFF",
    "Y":"GLIDE", "W":"GLIDE", "HH":"GLIDE",
}

def normalize_coda(coda: Tuple[str, ...]) -> Tuple[str, ...]:
    # collapse schwa+L spellings, treat AX/UL variants as L
    out: List[str] = []
    for ph in coda:
        if ph in {"UL"}:
            out.append("L")
        else:
            out.append(ph)
    # flap merge optional: nothing heavy; users can toggle if desired later
    return tuple(out)

def coda_family(coda: Tuple[str, ...]) -> str:
    if not coda: return "Ø"
    fams = [CODA_FAMILY.get(ph, ph) for ph in coda]
    return "+".join(fams)

# ---------------------- pronunciation resolver ----------------------

def cmu_or_none(word: str) -> List[List[str]]:
    try:
        return cmu_word_phones(word) or []
    except Exception:
        return []

def datamuse_phones(term: str) -> List[List[str]]:
    if dm is None: 
        return []
    try:
        # prefer exact spelling hit with md=r; fallback to sounds-like
        items = dm.words(sp=term, md="r", max_items=3) or []
        prons: List[List[str]] = []
        for it in items:
            for t in it.get("tags", []):
                if t.startswith("pron:"):
                    prons.append(t[5:].split())
        if not prons:
            items = dm.words(sl=term, md="r", max_items=5) or []
            for it in items:
                for t in it.get("tags", []):
                    if t.startswith("pron:"):
                        prons.append(t[5:].split())
        return prons
    except Exception:
        return []

def g2p_guess(term: str) -> List[List[str]]:
    # keep it optional to avoid heavy deps; return [] if not present
    try:
        from g2p_en import G2p
        g2p = G2p()
        seq = [p for p in g2p(term) if re.match(r"^[A-Z]{2}[012]?$", p)]
        return [seq] if seq else []
    except Exception:
        return []

def phones_for_term(term: str) -> List[str]:
    """
    Resolve pronunciation for single word or multiword term.
    For multiword inputs, return the phones of the LAST content word.
    """
    words = [w for w in re.findall(r"[A-Za-z']+", term.lower()) if w]
    if not words: return []
    # choose last content word
    content = words[-1]
    # CMU -> Datamuse -> g2p
    prons = cmu_or_none(content)
    if not prons:
        prons = datamuse_phones(content)
    if not prons:
        prons = g2p_guess(content)
    return prons[0] if prons else []

# ------------------------- rhyme keys --------------------------

def perfect_key(phones: List[str]) -> Tuple[str, Tuple[str, ...]]:
    nuc, stress = last_stressed_nucleus(phones)
    return (f"{nuc}{stress}", coda_of_last_syllable(phones))

def slant_key(phones: List[str], level: str = "B") -> Tuple:
    nuc, stress = last_stressed_nucleus(phones)
    coda = coda_of_last_syllable(phones)
    fam = coda_family(coda)
    if level.upper() == "A":
        return (nuc,)
    if level.upper() == "C":
        return (fam, stress)
    return (nuc, fam)

# ------------------------- candidates --------------------------

def candidate_ok(word: str) -> bool:
    if not re.match(r"^[A-Za-z][A-Za-z']*$", word): return False
    if len(word) <= 1 and word.lower() not in {"ax"}: return False
    return True

def rarity(word: str) -> float:
    z = zipf_freq(word)
    return 9.9 if z is None else z

def multiword_space() -> Iterable[Tuple[str, float]]:
    """
    Yield multiword phrases and an approximate rarity.
    You can back this with a cached list built at startup; for now
    we synthesize by combining uncommon words seen in CMU.
    """
    # Minimal safe stub: empty iterator means feature stays quiet.
    return []
# If you already have a phrase generator in your codebase,
# you can wire it here instead of returning [].

# --------------------------- ranking ---------------------------

def rank_score(src_phones: List[str], cand_phones: List[str]) -> Tuple[int,int,float,str]:
    # 1) stress match on last vowel (exact = better)
    s_nuc, s_str = last_stressed_nucleus(src_phones)
    c_nuc, c_str = last_stressed_nucleus(cand_phones)
    stress_match = 1 if s_str == c_str else 0
    # 2) syllable proximity (lower distance first)
    sd = abs(len(split_syllables(src_phones)) - len(split_syllables(cand_phones)))
    # 3) frequency (we sort by freq descending later, no need here)
    # 4) alpha
    return (stress_match, -sd, 0.0, "")  # placeholders to keep tuple shape stable

# --------------------------- search ----------------------------

def search(term: str, cfg: SearchConfig) -> Dict[str, List[Dict]]:
    q = (term or "").strip()
    if not q:
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}

    anchor = phones_for_term(q)
    if not anchor:
        # If totally unresolved, try Datamuse suggestions and bail gracefully
        return {"uncommon": [], "slant": [], "multiword": [], "rap_targets": []}

    # build keys for matching
    pkey = perfect_key(anchor)
    skey = slant_key(anchor, cfg.slant_level)

    # --------- enumerate your lexicon ----------
    # NOTE: assume you already have a function all_vocab_words() -> iterable[str]
    try:
        from rhyme_core.lexicon import all_vocab_words  # thin local iterator
    except ImportError:
        # Fallback if lexicon not available
        def all_vocab_words():
            return []
    
    strict: List[Tuple[str, List[str]]] = []
    slant: List[Tuple[str, List[str]]] = []

    for w in all_vocab_words():
        if not candidate_ok(w): continue
        phs = phones_for_term(w)  # resolves via CMU/Datamuse/g2p
        if not phs: continue
        if perfect_key(phs) == pkey:
            strict.append((w, phs))
        elif slant_key(phs, cfg.slant_level) == skey:
            slant.append((w, phs))

    # rarity filter + sort (most common → least) within cap
    def keep_and_tag(items: List[Tuple[str, List[str]]], zipf_cap: float) -> List[Dict]:
        filt = [(w, ph, rarity(w)) for (w, ph) in items if rarity(w) <= zipf_cap]
        # main order: most common first
        filt.sort(key=lambda t: (-t[2], rank_score(anchor, t[1]), t[0]))
        out = []
        for w, ph, z in filt[:cfg.max_items]:
            syls = len(split_syllables(ph))
            nuc, st = last_stressed_nucleus(ph)
            out.append({"word": w, "syl": syls, "zipf": z, "nuc": nuc, "stress": st})
        return out

    uncommon = keep_and_tag(strict, cfg.zipf_max_perfect)
    slant_out = keep_and_tag(slant, cfg.zipf_max_slant)

    # --------- multiword phrases ---------
    mres: List[Dict] = []
    for phrase, approx_z in multiword_space():
        if approx_z > cfg.zipf_max_multi: 
            continue
        last_word = phrase.split()[-1]
        ph = phones_for_term(last_word)
        if not ph: 
            continue
        if perfect_key(ph) != pkey and slant_key(ph, cfg.slant_level) != skey:
            continue
        mres.append({"word": phrase, "syl": None, "zipf": approx_z})
        if len(mres) >= cfg.max_items:
            break

    # rap targets left as-is (your existing logic), or empty
    rap_targets: List[Dict] = []

    return {"uncommon": uncommon, "slant": slant_out, "multiword": mres, "rap_targets": rap_targets}