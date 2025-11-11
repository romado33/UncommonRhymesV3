#!/usr/bin/env python3
"""Analyze Datamuse results to understand correct slant rhyme logic"""

import sqlite3
from rhyme_core.phonetics import parse_pron, rhyme_tail, k_keys

# Words from Datamuse slant rhymes for sister
datamuse_slant = ['whisper', 'figure', 'bitter', 'drifter', 'silver', 'litter', 'pitcher', 'mirror']

conn = sqlite3.connect('data/words_index.sqlite')
cur = conn.cursor()

print('Analyzing Datamuse slant rhymes for sister:')
print('sister: S IH1 S T ER0 (stressed: IH1, final: ER0)')
print()

for word in datamuse_slant:
    cur.execute('SELECT word, pron FROM words WHERE word = ?', (word,))
    result = cur.fetchone()
    if result:
        _, pron = result
        phones = parse_pron(pron)
        vowel_base, coda = rhyme_tail(phones)
        k1, k2, k3 = k_keys(phones)
        
        # Show which vowel is stressed
        stressed_vowels = [phone for phone in phones if phone[-1] in '12']
        final_vowel = None
        for phone in phones:
            if phone[-1] in '012' and phone == phones[-1]:
                final_vowel = phone
                break
        
        print(f'{word:10} {pron:15} (stressed: {stressed_vowels}, final: {final_vowel}, rhyme_base: {vowel_base})')

conn.close()
