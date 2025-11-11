#!/usr/bin/env python3
"""
Test for Real Rhymes - Check if database has actual rhymes or just identical words
"""

import sqlite3

def find_real_rhymes():
    conn = sqlite3.connect("songs_patterns_unified.db")
    cursor = conn.cursor()
    
    print("🔍 SEARCHING FOR REAL RHYMES (not identical words)...")
    
    # Find patterns where source_word != target_word (actual rhymes)
    cursor.execute("""
        SELECT pattern, artist, song_title, confidence_score
        FROM song_rhyme_patterns 
        WHERE source_word != target_word
        ORDER BY confidence_score DESC 
        LIMIT 20
    """)
    
    real_rhymes = cursor.fetchall()
    
    if real_rhymes:
        print(f"\n✅ FOUND {len(real_rhymes)} REAL RHYMES:")
        for pattern, artist, song, conf in real_rhymes:
            print(f"   • '{pattern}' - {artist} ({conf:.2f})")
    else:
        print(f"\n❌ NO REAL RHYMES FOUND - Only identical word matches")
    
    # Count identical vs real rhymes
    cursor.execute("SELECT COUNT(*) FROM song_rhyme_patterns WHERE source_word = target_word")
    identical = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM song_rhyme_patterns WHERE source_word != target_word") 
    different = cursor.fetchone()[0]
    
    total = identical + different
    
    print(f"\n📊 RHYME BREAKDOWN:")
    print(f"   • Identical words: {identical:,} ({(identical/total)*100:.1f}%)")
    print(f"   • Different words: {different:,} ({(different/total)*100:.1f}%)")
    
    if identical > different:
        print(f"\n❌ PROBLEM: Most 'rhymes' are identical words!")
        print(f"   The rhyme detection algorithm is broken.")
    else:
        print(f"\n✅ GOOD: More real rhymes than identical words.")
    
    conn.close()

if __name__ == "__main__":
    find_real_rhymes()
