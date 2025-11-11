# Rhyme Engine Theory Specification (K+R+Flow Model)
Version 1.0 — Draft  
Author: Rob Dods + AI Research Assistant  
License: MIT  
Status: In Development  

---
## Table of Contents
1. Purpose and Scope
2. Phonetic Foundations
   2.1 ARPABET Phoneme Inventory
   2.2 Vowel/Consonant Classes
   2.3 Stress System (0/1/2)
   2.4 Syllable Segmentation and Rime Structure
3. Rhyme Tail Theory
   3.1 Definition: Last Primary-Stressed Vowel
   3.2 Tail Extraction Algorithm
4. Rhyme Classification Taxonomy
   4.1 Perfect Rhyme (Strict)
   4.2 Loose Perfect Rhyme
   4.3 Terminal Rime Match (Compounds)
   4.4 Assonance (Tail)
   4.5 Consonance (Tail)
   4.6 Pararhyme (Consonant-Frame)
   4.7 Family Rhymes (Phonological Equivalence)
   4.8 Multisyllabic Rhymes (Multis)
   4.9 Internal Rhyme (Intra-line)
   4.10 Upstream Assonance (Pre-tail)
   4.11 Wrenched/Forced Rhymes
   4.12 Eye Rhymes (Visual; Exclude)
   4.13 Homophone Rhymes
5. The K-Key Model (Core)
   5.1 K3: Strict Perfect
   5.2 K2: Loose Perfect (Stress-Agnostic)
   5.3 K2.5: Terminal Match (Compounds)
   5.4 K1: Tail Assonance
   5.5 K0: Upstream Assonance
6. Extended Phonetic Match Categories
   6.1 KC: Tail Consonance
   6.2 KF: Family-Consonant Equivalence
   6.3 KP: Pararhyme Match
   6.4 KM: Multisyllabic Continuity
7. Rhyme Rarity (R-Keys)
   7.1 KR: Tail Rarity Index
   7.2 Frequency Normalization Logic
8. Scoring Specification
   8.1 Weighted Rhyme Scoring Formula
   8.2 Confidence Adjustment
   8.3 Edge Case Overrides
9. Similarity Layers
   9.1 Phonetic Edit Distance (Phones/Features)
   9.2 Stress Alignment Penalty
   9.3 Phoneme Feature Distance (Place/Manner/Voicing)
10. Multiword and Phrase Handling
    10.1 Compound Word Alignment
    10.2 Phrase-Level Tail Extraction
    10.3 Function-Word Filtering
11. Rap Flow Extensions
    11.1 Rhyme Density
    11.2 Multiset Rhyme Chains & Lattices
    11.3 Cross-Bar Rhymes
    11.4 Scheme Scoring (AABB, ABAB, AAAA, etc.)
12. Semantic Alignment Extensions
    12.1 Topic Continuity
    12.2 Punchline Support (Setup→Twist)
    12.3 Sentiment/Theme Cohesion
13. Evaluation Dataset Specification
    13.1 Annotation Schema
    13.2 Test Suite
    13.3 Human Alignment Metrics
14. LLM Prompt Alignment Rules
    14.1 Rhyming Output API Protocol
    14.2 Rhyme Consistency Constraints
    14.3 Structured Output Blocks
15. Structured Rhyme Definitions (YAML Spec Library)
16. Example Annotations
17. Glossary
18. Appendix: Phoneme Class Tables
19. References

---

# 1. Purpose and Scope
This specification defines a complete, phonetics-based rhyme theory and an evaluation model (**K+R+Flow**) suitable for implementation in rule-based systems and LLM toolchains. It standardizes terminology, matching logic, and scoring to ensure reproducible rhyme judgments across poetry, lyrics, and generative AI systems.

---

# 2. Phonetic Foundations

## 2.1 ARPABET Phoneme Inventory
Operate on ARPABET phones with optional stress digits on vowels. Example vowel set: `AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW`.

## 2.2 Vowel/Consonant Classes
- **Vowels**: carry stress (`0/1/2`).  
- **Consonants**: no stress; grouped by **place** (labial, dental, alveolar, palatal, velar, glottal), **manner** (stop, fricative, affricate, nasal, liquid, glide), and **voicing**.

## 2.3 Stress System
- `1` primary, `2` secondary, `0` unstressed.  
- Use the **last primary-stressed vowel** as the rhyme anchor by default.

## 2.4 Syllable Segmentation and Rime Structure
- **Onset**: consonants before nucleus.  
- **Nucleus**: vowel (carries stress).  
- **Coda**: consonants after the nucleus.  
- **Rime** = nucleus + coda.  
- **Rhyme tail** (in this spec) = from the **last primary-stressed vowel** (inclusive) to end of the word/phrase.

---

# 3. Rhyme Tail Theory

## 3.1 Definition: Last Primary-Stressed Vowel
Let `V1` be the index of the last vowel with stress `1`. If absent (rare), strict perfect rhyme is **not** computed. Implementers MAY define a fallback to `2` in a separate, non-strict mode.

## 3.2 Tail Extraction Algorithm (Formal)
**Input**: Phones with stress.  
**Output**: `tail(word)` = phones `[V1 … end]`.

Rules:
1. Find last `1`-stressed vowel (V1).  
2. Tail begins at that vowel (including stress digit) and includes all following phones.  
3. For phrase-level, compute on the **final content word** unless explicitly configured otherwise.

**Example**:  
- *without* → `W IH0 DH AW1 T` → tail = `AW1 T`.  
- *devout* → `D IH0 V AW1 T` → tail = `AW1 T` (perfect vs *without*).

---

# 4. Rhyme Classification Taxonomy

## 4.1 Perfect Rhyme (Strict)
**Definition**: `tail(A) == tail(B)` (including stress digits).  
**Example**: *without/devout/about/doubt/shout* → `AW1 T` tails.

## 4.2 Loose Perfect Rhyme (Stress-Agnostic)
**Definition**: vowel class + coda match with **stress digits ignored**.  
**Example**: *without/workout* (`AW T` matches; stress differs).

## 4.3 Terminal Rime Match (Compounds)
**Definition**: Final-syllable rime equality (e.g., `AW T`) even if the **last primary stress** lies earlier in a compound/hyphenation.  
**Example**: *without/stakeout* (`AW T` final syllable match; tails differ) → terminal, not perfect.

## 4.4 Assonance (Tail)
**Definition**: Last-stressed vowel quality match only, ignoring coda.  
**Example**: *seen/feet* (IY vs IY; codas differ).

## 4.5 Consonance (Tail)
**Definition**: Coda consonant(s) match while vowels differ.  
**Example**: *milk/walk* (final `K` consonance).

## 4.6 Pararhyme (Consonant-Frame)
**Definition**: Onset and coda consonants match while vowel quality differs.  
**Example**: *pad/pod* (P-D frame same; vowel differs).

## 4.7 Family Rhymes (Phonological Equivalence)
**Definition**: Mismatch allowed within same **place/manner/voicing family** (e.g., /T/~/**D**; /F/~/**V**).  
**Example**: *dad/bad* (labial stop family proximity).

## 4.8 Multisyllabic Rhymes (Multis)
**Definition**: Two or more consecutive syllables rhyme by K2+ rules; can span words.  
**Example**: *battery acid* / *cavalry jacket* (multi-syllabic cadence).

## 4.9 Internal Rhyme (Intra-line)
**Definition**: A stressed syllable within a line rhymes with another stressed position within the same line.  
**Example**: *“I **spray** then I **pray** they **pay** today.”*

## 4.10 Upstream Assonance (Pre-tail)
**Definition**: Shared vowel quality **before** the rhyme tail (pre-`V1`). Not a rhyme; a cohesion feature.  
**Example**: *guitar/designer* (`IH` upstream match).

## 4.11 Wrenched/Forced Rhymes
**Definition**: Stress is reinterpreted/shifted to force an apparent rhyme. Low credibility; detectable but penalized.

## 4.12 Eye Rhymes (Visual; Exclude)
**Definition**: Spelling-only matches; pronunciation differs.  
**Example**: *love/move*, *cough/though* — reject.

## 4.13 Homophone Rhymes
**Definition**: Identical pronunciations by any lexicon entry; treated as **perfect** if the same tail is realized.  
**Note**: Weight down for overuse if diversity is desired.

---

# 5. The K-Key Model (Core)

## 5.1 K3 — Strict Perfect
**Rule**: `tail(A) == tail(B)` including stress digit(s).  
**Return**: `K3=true` else false.

## 5.2 K2 — Loose Perfect (Stress-Agnostic)
**Rule**: Strip stress digits from tail; equality on vowel class + coda.  
**Return**: `K2=true` else false.

## 5.3 K2.5 — Terminal Rime (Compounds)
**Rule**: Final-syllable rime equality (`nucleus + coda`) even if last-primary tail differs.  
**Return**: `K2_5=true` else false.

## 5.4 K1 — Tail Assonance
**Rule**: Last-stressed vowel class equality; ignore coda.  
**Return**: `K1=true` else false.

## 5.5 K0 — Upstream Assonance
**Rule**: Shared vowel class(es) upstream of `V1`.  
**Return**: `K0 ∈ [0.10, 0.25]` based on overlap count/alignment.

---

# 6. Extended Phonetic Match Categories (K+)

## 6.1 KC — Tail Consonance
**Rule**: Overlap of coda consonants in the tail while vowels differ. Weight by cluster length and order.

## 6.2 KF — Family-Consonant Equivalence
**Rule**: Replace consonants with **feature classes** (place/manner/voicing) and compute equivalence overlap. E.g., /T/~/**D**, /S/~/**Z**.

## 6.3 KP — Pararhyme Match
**Rule**: Onset+coda consonant frame match, vowel mismatch allowed. Penalize by vowel distance (feature space).

## 6.4 KM — Multisyllabic Continuity
**Rule**: Consecutive syllable matches at K2 or stronger. Score scales with span length and stress alignment.

---

# 7. Rhyme Rarity (R-Keys)

## 7.1 KR — Tail Rarity Index
**Definition**: `KR = 1 - freq_norm(tail_class)`; higher when rhyme tail is rare.  
**Tail class** example: `(vowel_base + coda_no_stress)`, e.g., `AW|T`.

## 7.2 Frequency Normalization Logic
- Compute frequencies over a balanced corpus (lexicon or lyrics).  
- Apply smoothing for unseen tails; clamp to `[0.0, 1.0]`.  
- Optionally compute **per-genre KR** (rap vs general English).

---

# 8. Scoring Specification

## 8.1 Weighted Rhyme Score (WRS)
Let:
- `S_K3 ∈ {0,1}`, `S_K2 ∈ {0,1}`, `S_K2_5 ∈ {0,1}`, `S_K1 ∈ {0,1}`, `S_K0 ∈ [0,0.25]`
- `S_KC, S_KF, S_KP, S_KM ∈ [0,1]` (normalized)
- `KR ∈ [0,1]`

**WRS** (one plausible default):
```
WRS =
  1.00*S_K3
+ 0.85*(1-S_K3)*S_K2
+ 0.60*(1-S_K3)*(1-S_K2)*S_K2_5
+ 0.35*(1-S_K3)*(1-S_K2)*(1-S_K2_5)*S_K1
+ 0.20*S_KC
+ 0.15*S_KF
+ 0.15*S_KP
+ 0.10*min(S_KM, 1.0)
+ S_K0            # 0.10..0.25 if present
+ 0.20*KR
```
Clamp to `[0.0, 1.0]`. Tune weights per application.

## 8.2 Confidence Adjustment
- Downweight if lexicon ambiguity is high (many variants).  
- Upweight if multiple independent rules agree (e.g., K3 + KM).

## 8.3 Edge Case Overrides
- If `S_K3=1`, force `WRS ≥ 0.95`.  
- If eye-rhyme detected, set `WRS = 0` unless homophone also true.

---

# 9. Similarity Layers

## 9.1 Phonetic Edit Distance
Compute Levenshtein on phone sequences in the tail (stress-aware or stressless modes). Normalize by length.

## 9.2 Stress Alignment Penalty
Penalty if stress positions differ across tails even when phones match loosely.

## 9.3 Phoneme Feature Distance
Feature vector per consonant (place/manner/voicing) and vowel (height/backness/rounding, approximated via ARPABET mapping). Use Hamming or weighted distance for KF/KP scoring.

---

# 10. Multiword and Phrase Handling

## 10.1 Compound Word Alignment
For hyphenations/compounds (e.g., *stakeout*), compute both:
- **Tail-based** (strict) using last primary-stressed position.  
- **Terminal rime** of final syllable for K2.5.

## 10.2 Phrase-Level Tail Extraction
By default, rhyme against the **final content word**. Optionally include enclitics if stressed (dialectal).

## 10.3 Function-Word Filtering
Ignore upstream vowels from stop-words (`a, the, of`) for K0 to reduce noise.

---

# 11. Rap Flow Extensions

## 11.1 Rhyme Density
Rhyme tokens per 10 syllables or per bar. Count K2+ as core; K1/K0 as auxiliaries.

## 11.2 Multiset Rhyme Chains & Lattices
Graph of rhyme events across bars; edges connect repeated tails or families. Score continuity.

## 11.3 Cross-Bar Rhymes
Reward tails recurring across line breaks (end→beginning or end→end).

## 11.4 Scheme Scoring
Detect schemes (AABB/ABAB/AAAA). Bonus for complexity and stability.

---

# 12. Semantic Alignment Extensions

## 12.1 Topic Continuity
Cosine similarity between line embeddings; reward when rhymed lines stay on-topic.

## 12.2 Punchline Support (Setup→Twist)
Detect setup line leading to twist/punch on the rhyme line (semantic surprise).

## 12.3 Sentiment/Theme Cohesion
Align sentiment trajectory across rhymed positions; overuse of homophones may be penalized if semantic redundancy is high.

---

# 13. Evaluation Dataset Specification

## 13.1 Annotation Schema (Overview)
Annotate pairs with:
- Phones, stress, tails
- K3/K2/K2.5/K1/K0 flags
- KC/KF/KP/KM metrics
- KR (rarity)
- Human judgment: {perfect, near, slant, not rhyme}, 5-point quality

## 13.2 Test Suite
- Minimal pairs per category
- Compounds vs strict tails
- Dialectal variants
- Multisyllabic spans

## 13.3 Human Alignment Metrics
- Krippendorff’s alpha for category agreement
- Rank correlation (Spearman) between WRS and human scores

---

# 14. LLM Prompt Alignment Rules

## 14.1 Rhyming Output API Protocol (LLM-Facing)
**Contract**: When asked to rhyme a target, the LLM SHOULD emit a JSON block with:
```json
{
  "target": "without",
  "phones": "W IH0 DH AW1 T",
  "tail": "AW1 T",
  "rhyme_scheme": "AABB",
  "pairs": [
    {"word":"devout","why":"K3 tail AW1 T"},
    {"word":"about","why":"K3 tail AW1 T"},
    {"word":"stakeout","why":"K2.5 terminal AW T (not strict)"}
  ]
}
```

## 14.2 Rhyme Consistency Constraints
- Prefer K3 for “perfect” unless explicitly relaxed.  
- Avoid eye rhymes unless requested.  
- Report stress positions and tails.

## 14.3 Structured Output Blocks
Emit reason strings citing K-keys (e.g., `K3`, `K2.5`, `K0`) to assist downstream scoring.

---

# 15. Structured Rhyme Definitions (YAML Spec Library)

```yaml
perfect_rhyme_strict:
  id: K3
  definition: "Tail equality from last primary-stressed vowel inclusive, with stress digits."
  input: ["phones_A", "phones_B"]
  output: { is_match: boolean, tail: string }
  examples:
    - A: "without (W IH0 DH AW1 T)"
      B: "devout (D IH0 V AW1 T)"
      result: true
      note: "Tail AW1 T equals"
loose_perfect:
  id: K2
  definition: "Tail equality ignoring stress digits."
  examples:
    - A: "without"
      B: "workout"
      result: true
terminal_match:
  id: K2.5
  definition: "Final-syllable rime equality when last primary occurs earlier."
assonance_tail:
  id: K1
  definition: "Last stressed vowel equality; ignore coda."
upstream_assonance:
  id: K0
  definition: "Shared vowel classes pre-tail; not a rhyme."
tail_consonance:
  id: KC
  definition: "Coda consonant overlap with differing vowels."
family_rhyme:
  id: KF
  definition: "Consonant equivalence by place/manner/voicing."
pararhyme:
  id: KP
  definition: "Same onset+coda frame; vowel differs."
multisyllabic:
  id: KM
  definition: "Two or more consecutive syllables match at K2+."
rarity_index:
  id: KR
  definition: "Rarity of the (vowel_base+coda) tail class; 1 is rarest."
```

---

# 16. Example Annotations

**Target**: *without* → `W IH0 DH AW1 T` → tail `AW1 T`

| Word | Phones | Class | Reason |
|------|--------|-------|--------|
| devout | D IH0 V AW1 T | **K3** | Same tail `AW1 T` |
| about | AH0 B AW1 T | **K3** | Same tail |
| doubt | D AW1 T | **K3** | Same tail |
| workout | W ER1 K AW2 T | **K2** | Stress ignored: `AW T` |
| stakeout | S T EY1 K AW2 T | **K2.5** | Final `AW T` only |
| shoot | SH UW1 T | — | Vowel mismatch |
| within | W IH0 DH IH1 N | **K0** | Upstream IH match only |

**Internal/Upstream**:  
- *guitar* `G IH0 T AA1 R` vs *designer* `D IH0 Z AY1 N ER0` → **K0** via `IH` upstream; no rhyme.

**Multis**:  
- *history* / *mystery* → 2-syllable K2 match.  
- *battery acid* / *cavalry jacket* → 3+ syllable KM continuity.

---

# 17. Glossary
- **ARPABET**: ASCII phoneme set used in CMUdict.  
- **Tail**: Phones from last primary-stressed vowel to end.  
- **Rime**: Syllable nucleus + coda.  
- **Pararhyme**: Consonant-frame equality with vowel change.  
- **Family Rhyme**: Match by phonological feature classes.  
- **KR**: Rarity score of a tail class.

---

# 18. Appendix: Phoneme Class Tables

## 18.1 Vowel Classes (ARPABET → Broad Features)
| Vowel | Height | Backness | Round | Notes |
|------|--------|---------|-------|-------|
| IY | high | front | unrounded | as in *fleece* |
| IH | high | front | unrounded | *kit* |
| EY | mid | front | unrounded | *face* |
| EH | mid | front | unrounded | *dress* |
| AE | low | front | unrounded | *trap* |
| AA | low | back | unrounded | *spa* |
| AO | mid | back | rounded | *thought* |
| OW | mid | back | rounded | *goat* |
| UH | high | back | rounded | *foot* |
| UW | high | back | rounded | *goose* |
| ER | mid | central | rhotic | *nurse* |
| AH | mid | central | unrounded | *strut* |
| AW | diphthong | backish | rounded glide | *mouth* |
| AY | diphthong | frontish | unrounded glide | *price* |
| OY | diphthong | back→front | rounded glide | *choice* |

## 18.2 Consonant Classes (Place/Manner/Voicing)
| Phone | Place | Manner | Voice |
|------|-------|--------|-------|
| P | bilabial | stop | voiceless |
| B | bilabial | stop | voiced |
| T | alveolar | stop | voiceless |
| D | alveolar | stop | voiced |
| K | velar | stop | voiceless |
| G | velar | stop | voiced |
| CH | postalveolar | affricate | voiceless |
| JH | postalveolar | affricate | voiced |
| F | labiodental | fricative | voiceless |
| V | labiodental | fricative | voiced |
| TH | dental | fricative | voiceless |
| DH | dental | fricative | voiced |
| S | alveolar | fricative | voiceless |
| Z | alveolar | fricative | voiced |
| SH | postalveolar | fricative | voiceless |
| ZH | postalveolar | fricative | voiced |
| HH | glottal | fricative | voiceless |
| M | bilabial | nasal | voiced |
| N | alveolar | nasal | voiced |
| NG | velar | nasal | voiced |
| L | alveolar | liquid | voiced |
| R | alveolar | liquid (rhotic) | voiced |
| W | bilabial/velar | glide | voiced |
| Y | palatal | glide | voiced |

---

# 19. References
- CMU Pronouncing Dictionary (CMUdict).  
- Hayes, Bruce. *Introductory Phonology*.  
- McCarthy & Prince. *Prosodic Morphology*.  
- Kiparsky, Paul. “Rhyme and Meter.”  
- Hip-hop rhyme analysis literature (various).

---

**Implementation Notes (Non-normative):**
- Always compare **phonemes**, never raw spelling.  
- Allow multiple pronunciations; a K3 match exists if **any** pronunciation pair matches.  
- For evaluation, prefer conservative defaults: K3 = “perfect,” K2 = “near-perfect,” K2.5 = “terminal,” K1 = “assonance,” K0 = “upstream-only.”
