#!/usr/bin/env python3
"""
Deep Diagnostic: Trace exactly where the search is failing
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, r"C:\Users\RobDods\apps\uncommonrhymesv3")

print("=" * 70)
print("🔬 DEEP DIAGNOSTIC: Tracing Search Failure")
print("=" * 70)

# Test 1: Database lookup
print("\n1️⃣ Testing direct database lookup for 'double'...")
try:
    import sqlite3
    from rhyme_core.data.paths import words_db
    
    db_path = words_db()
    print(f"   Database path: {db_path}")
    print(f"   Exists: {db_path.exists()}")
    
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Try to find "double"
        cursor.execute(
            "SELECT word, pron, k1, k2, k3, zipf, syls, stress FROM words WHERE word = 'double'"
        )
        row = cursor.fetchone()
        
        if row:
            print(f"   ✅ Found 'double' in database:")
            print(f"      word: {row['word']}")
            print(f"      pron: {row['pron']}")
            print(f"      k1: {row['k1']}")
            print(f"      k2: {row['k2']}")
            print(f"      k3: {row['k3']}")
            print(f"      zipf: {row['zipf']}")
            print(f"      syls: {row['syls']}")
            print(f"      stress: {row['stress']}")
        else:
            print(f"   ❌ 'double' NOT FOUND in database!")
            print(f"   Checking if ANY words exist...")
            cursor.execute("SELECT COUNT(*) as cnt FROM words")
            count = cursor.fetchone()['cnt']
            print(f"   Total words in database: {count}")
            
            # Check for similar words
            cursor.execute("SELECT word FROM words WHERE word LIKE 'doub%' LIMIT 5")
            similar = cursor.fetchall()
            print(f"   Words starting with 'doub': {[r['word'] for r in similar]}")
        
        conn.close()
    else:
        print(f"   ❌ Database file not found!")
        
except Exception as e:
    print(f"   ❌ Database test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Check what parse_pron returns
print("\n2️⃣ Testing parse_pron behavior...")
try:
    from rhyme_core.phonetics import parse_pron
    
    # Test with word
    result1 = parse_pron("double")
    print(f"   parse_pron('double') = {result1}")
    
    # Test with pronunciation string
    result2 = parse_pron("D AH1 B AH0 L")
    print(f"   parse_pron('D AH1 B AH0 L') = {result2}")
    
except Exception as e:
    print(f"   ❌ parse_pron test failed: {e}")

# Test 3: Test the database fallback function
print("\n3️⃣ Testing _get_pronunciation_from_db function...")
try:
    from rhyme_core.search import _get_pronunciation_from_db
    
    result = _get_pronunciation_from_db("double")
    print(f"   _get_pronunciation_from_db('double') = {result}")
    
    if result:
        print(f"   ✅ Database fallback works!")
    else:
        print(f"   ❌ Database fallback returned None!")
        
except ImportError as e:
    print(f"   ⚠️  Function not found in search module: {e}")
    print(f"   This means you might not have installed search_FIXED_FINAL.py yet!")
except Exception as e:
    print(f"   ❌ Database fallback test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test phoneme validation function
print("\n4️⃣ Testing _is_valid_phoneme_list function...")
try:
    from rhyme_core.search import _is_valid_phoneme_list
    
    test1 = _is_valid_phoneme_list(['double'])
    print(f"   _is_valid_phoneme_list(['double']) = {test1}")
    print(f"   Expected: False ✓" if not test1 else "   Expected: False ✗")
    
    test2 = _is_valid_phoneme_list(['D', 'AH1', 'B', 'AH0', 'L'])
    print(f"   _is_valid_phoneme_list(['D', 'AH1', 'B', 'AH0', 'L']) = {test2}")
    print(f"   Expected: True ✓" if test2 else "   Expected: True ✗")
    
except ImportError as e:
    print(f"   ⚠️  Function not found in search module: {e}")
    print(f"   This means you might not have installed search_FIXED_FINAL.py yet!")
except Exception as e:
    print(f"   ❌ Validation test failed: {e}")

# Test 5: Full integration test with search_all_categories
print("\n5️⃣ Testing full search_all_categories flow...")
try:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    from rhyme_core.search import search_all_categories
    
    print("   Calling search_all_categories('double', max_items=5)...")
    print("   " + "-" * 66)
    
    result = search_all_categories('double', max_items=5)
    
    print("   " + "-" * 66)
    print(f"\n   Results:")
    print(f"   Uncommon: {len(result['uncommon'])} items")
    print(f"   Slant: {len(result['slant'])} items")
    print(f"   Multiword: {len(result['multiword'])} items")
    
    if result['uncommon']:
        print(f"\n   First 5 uncommon rhymes:")
        for i, item in enumerate(result['uncommon'][:5], 1):
            print(f"      {i}. {item.get('word')} (zipf: {item.get('zipf')})")
    else:
        print(f"\n   ❌ No uncommon rhymes found!")
    
except Exception as e:
    print(f"   ❌ Search test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("🎯 DIAGNOSTIC COMPLETE")
print("=" * 70)
