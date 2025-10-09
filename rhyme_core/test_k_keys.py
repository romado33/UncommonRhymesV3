"""
Test script for updated k_keys function with proper K3 implementation.

This demonstrates the rhyme strength hierarchy:
- K3 match: Strict perfect (same stress + same sounds)
- K2 match: Perfect by ear (different stress, same sounds)
- K1 match: Assonance only (same vowel)
"""

import sys
sys.path.insert(0, '/home/claude')

from phonetics import k_keys, parse_pron

# Test cases
test_words = {
    "double": "D AH1 B AH0 L",
    "trouble": "T R AH1 B AH0 L",
    "stubble": "S T AH1 B AH0 L",
    "bubble": "B AH1 B AH0 L",
    "rubble": "R AH1 B AH0 L",
    "couple": "K AH1 P AH0 L",
    "supple": "S AH1 P AH0 L",
    "cuddle": "K AH1 D AH0 L",
    "muddle": "M AH1 D AH0 L",
    "puzzle": "P AH1 Z AH0 L",
}

print("=" * 80)
print("K-KEYS TEST: Proper K3 Implementation")
print("=" * 80)
print()

print("Query word: 'double' /D AH1 B AH0 L/")
print()

query_phones = parse_pron(test_words["double"])
query_k1, query_k2, query_k3 = k_keys(query_phones)

print(f"Query k-keys:")
print(f"  k1 = '{query_k1}'  (vowel nucleus only)")
print(f"  k2 = '{query_k2}'  (stress-agnostic: vowel + tail)")
print(f"  k3 = '{query_k3}'  (stress-preserved: vowel WITH stress + tail)")
print()
print("=" * 80)
print()

# Test each candidate
results = {
    "K3 Matches (Strict Perfect - Score 1.00)": [],
    "K2 Matches Only (Perfect by Ear - Score 0.85)": [],
    "K1 Matches Only (Assonance - Score 0.35)": [],
    "No Match": []
}

for word, pron in test_words.items():
    if word == "double":
        continue  # Skip query word itself
    
    phones = parse_pron(pron)
    k1, k2, k3 = k_keys(phones)
    
    # Determine match type
    if k3 == query_k3:
        category = "K3 Matches (Strict Perfect - Score 1.00)"
    elif k2 == query_k2:
        category = "K2 Matches Only (Perfect by Ear - Score 0.85)"
    elif k1 == query_k1:
        category = "K1 Matches Only (Assonance - Score 0.35)"
    else:
        category = "No Match"
    
    results[category].append({
        "word": word,
        "pron": pron,
        "k1": k1,
        "k2": k2,
        "k3": k3
    })

# Display results
for category, matches in results.items():
    if matches:
        print(f"{category}")
        print("-" * 80)
        for match in matches:
            print(f"  {match['word']:12} /{match['pron']:20}/ → k3='{match['k3']}'")
        print()

# Additional explanations
print("=" * 80)
print("EXPLANATION")
print("=" * 80)
print()
print("K3 (Strict Perfect):")
print("  - Matches: trouble, stubble, bubble, rubble")
print("  - Why: All have AH1 (stressed AH) + B AH0 L tail")
print("  - Score: 1.00 (highest)")
print()
print("K2 (Perfect by Ear):")
print("  - Would match: Words with AH (any stress) + B AH0 L tail")
print("  - Example: If 'double' had different stress (/D AH0 B AH1 L/)")
print("  - Score: 0.85 (very strong, just stress differs)")
print()
print("K1 (Assonance):")
print("  - Matches: couple, supple, cuddle, muddle, puzzle")
print("  - Why: All have AH vowel nucleus, but different tails")
print("  - couple: AH|P AH0 L (P instead of B)")
print("  - cuddle: AH|D AH0 L (D instead of B)")
print("  - puzzle: AH|Z AH0 L (Z instead of B)")
print("  - Score: 0.35 (weak, vowel-only match)")
print()
print("=" * 80)
print()
print("KEY INSIGHT:")
print("  K3 distinguishes stress patterns → 'strict perfect' for poetry/rap")
print("  K2 ignores stress → 'perfect by ear' for most songwriting")
print("  K1 captures assonance → 'vowel echoes' for slant rhyming")
print()
print("=" * 80)
