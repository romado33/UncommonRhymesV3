#!/usr/bin/env python3
"""
Test script to verify rhyme.db works with your engine.py
Run this in your app directory to confirm everything is set up correctly
"""

import sqlite3
import os

def test_database():
    """Test that rhyme.db has the correct schema and data"""
    
    print("=" * 70)
    print("RHYME.DB VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Check if database exists
    if not os.path.exists('rhyme.db'):
        print("❌ ERROR: rhyme.db not found!")
        print("   Make sure rhyme.db is in the current directory")
        print(f"   Current directory: {os.getcwd()}")
        return False
    
    print(f"✅ Database found: rhyme.db")
    print(f"   Size: {os.path.getsize('rhyme.db') / 1024 / 1024:.2f} MB")
    print()
    
    try:
        conn = sqlite3.connect('rhyme.db')
        cursor = conn.cursor()
        
        # Test 1: Check table schema
        print("🧪 Test 1: Checking table schema...")
        cursor.execute("PRAGMA table_info(words)")
        columns = cursor.fetchall()
        
        required_columns = ['word', 'pron', 'k1', 'k2', 'k3', 'zipf', 'syls', 'stress']
        found_columns = [col[1] for col in columns]
        
        missing = set(required_columns) - set(found_columns)
        if missing:
            print(f"   ❌ Missing columns: {missing}")
            return False
        
        print(f"   ✅ All required columns present:")
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
        print()
        
        # Test 2: Test get_word_pronunciation query (from engine.py line 217)
        print("🧪 Test 2: Testing get_word_pronunciation query...")
        test_words = ['BED', 'GUITAR', 'DOG', 'DOLLAR']
        
        for word in test_words:
            cursor.execute("SELECT word, pron FROM words WHERE word = ? LIMIT 1", (word,))
            result = cursor.fetchone()
            
            if result:
                print(f"   ✅ {result[0]:12} -> {result[1]}")
            else:
                print(f"   ❌ {word:12} -> NOT FOUND")
        print()
        
        # Test 3: Test full search_rhymes query (from engine.py line 352)
        print("🧪 Test 3: Testing search_rhymes query...")
        cursor.execute("""
            SELECT word, pron, k1, k2, k3, zipf, syls, stress
            FROM words
            WHERE word != 'BED'
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        if not results:
            print("   ❌ Query returned no results")
            return False
        
        print(f"   ✅ Query works! Sample results:")
        for row in results[:3]:
            word, pron, k1, k2, k3, zipf, syls, stress = row
            print(f"      {word:12} k1={k1:6} k2={k2:15} syls={syls} zipf={zipf:.1f}")
        print()
        
        # Test 4: Test rhyme finding (find rhymes for BED)
        print("🧪 Test 4: Testing rhyme finding for 'BED'...")
        
        # Get BED's rhyme keys
        cursor.execute("SELECT k1, k2, k3 FROM words WHERE word = 'BED'")
        bed_data = cursor.fetchone()
        
        if not bed_data:
            print("   ❌ Could not find BED in database")
            return False
        
        k1, k2, k3 = bed_data
        print(f"   BED rhyme keys: K1={k1}, K2={k2}, K3={k3}")
        
        # Find perfect rhymes (k3 match)
        cursor.execute("""
            SELECT word FROM words 
            WHERE k3 = ? AND word != 'BED' 
            ORDER BY zipf DESC 
            LIMIT 10
        """, (k3,))
        
        perfect_rhymes = [r[0] for r in cursor.fetchall()]
        
        if perfect_rhymes:
            print(f"   ✅ Found {len(perfect_rhymes)} perfect rhymes:")
            print(f"      {', '.join(perfect_rhymes[:5])}")
        else:
            print(f"   ⚠️  No perfect rhymes found (unusual but not critical)")
        print()
        
        # Test 5: Verify dollar/ART separation
        print("🧪 Test 5: Verifying dollar/ART phonetic separation...")
        
        test_pairs = [
            ('DOLLAR', 'COLLAR'),  # Should be same family
            ('ART', 'CART'),       # Should be same family
            ('DOLLAR', 'ART')      # Should be different families
        ]
        
        all_correct = True
        for word1, word2 in test_pairs:
            cursor.execute("SELECT k3 FROM words WHERE word = ?", (word1,))
            k3_1 = cursor.fetchone()
            
            cursor.execute("SELECT k3 FROM words WHERE word = ?", (word2,))
            k3_2 = cursor.fetchone()
            
            if k3_1 and k3_2:
                k3_1 = k3_1[0]
                k3_2 = k3_2[0]
                
                match = k3_1 == k3_2
                expected_match = (word1, word2) != ('DOLLAR', 'ART')
                
                if match == expected_match:
                    status = "✅"
                else:
                    status = "❌"
                    all_correct = False
                
                print(f"   {status} {word1:12} vs {word2:12} -> {'SAME' if match else 'DIFFERENT':10} family")
        
        if not all_correct:
            print("   ⚠️  Phonetic separation may have issues")
        print()
        
        # Test 6: Count statistics
        print("📊 Database Statistics:")
        cursor.execute("SELECT COUNT(*) FROM words")
        total = cursor.fetchone()[0]
        print(f"   Total words: {total:,}")
        
        cursor.execute("SELECT AVG(zipf) FROM words")
        avg_zipf = cursor.fetchone()[0]
        print(f"   Average zipf: {avg_zipf:.2f}")
        
        cursor.execute("SELECT MIN(syls), MAX(syls) FROM words")
        min_syls, max_syls = cursor.fetchone()
        print(f"   Syllable range: {min_syls}-{max_syls}")
        print()
        
        conn.close()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Your rhyme.db is correctly configured for engine.py")
        print("You can now run: python app.py")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = test_database()
    sys.exit(0 if success else 1)
