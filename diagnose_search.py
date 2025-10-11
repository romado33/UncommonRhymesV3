#!/usr/bin/env python3
"""
Emergency Diagnostic Script - Find What's Broken

This script will test each component to find where the search is failing.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("🔍 RhymeRarity Emergency Diagnostics")
print("=" * 70)

# Test 1: Database Connection
print("\n[TEST 1] Database Connection")
try:
    db_path = Path("data/words_index.sqlite")
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path.absolute()}")
    else:
        print(f"✓ Database found at: {db_path.absolute()}")
        
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Check table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        if cur.fetchone():
            print("✓ 'words' table exists")
        else:
            print("❌ 'words' table NOT found")
            sys.exit(1)
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM words")
        count = cur.fetchone()[0]
        print(f"✓ Database has {count:,} words")
        
        # Get sample words
        cur.execute("SELECT word, pron, k1, k2, k3 FROM words LIMIT 5")
        print("\n  Sample database entries:")
        for row in cur.fetchall():
            word, pron, k1, k2, k3 = row
            print(f"    word={word}, pron={pron[:30]}..., k1={k1}, k2={k2[:20]}..., k3={k3[:20]}...")
        
        conn.close()
        print("✓ Database connection working\n")
except Exception as e:
    print(f"❌ Database error: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Phonetics Module
print("[TEST 2] Phonetics Module - K-Key Generation")
try:
    from rhyme_core.phonetics import k_keys, parse_pron
    
    # Test critical words
    test_cases = [
        ("dollar", "D AA1 L ER0"),
        ("collar", "K AA1 L ER0"),
        ("chart", "CH AA1 R T"),
        ("dart", "D AA1 R T"),
    ]
    
    k_results = {}
    for word, pron in test_cases:
        phones = parse_pron(pron)
        keys = k_keys(phones)
        k_results[word] = keys
        print(f"  {word:10} pron={pron:20} → k1={keys[0]:10} k2={keys[1][:20]:20} k3={keys[2][:20]:20}")
    
    # Validate phonetic families
    dollar_k1 = k_results["dollar"][0]
    collar_k1 = k_results["collar"][0]
    chart_k1 = k_results["chart"][0]
    dart_k1 = k_results["dart"][0]
    
    print(f"\n  Phonetic Family Check:")
    print(f"    Dollar family (should match): dollar k1={dollar_k1}, collar k1={collar_k1} → {'✓' if dollar_k1 == collar_k1 else '❌'}")
    print(f"    Chart family (should match): chart k1={chart_k1}, dart k1={dart_k1} → {'✓' if chart_k1 == dart_k1 else '❌'}")
    print(f"    No contamination: dollar k1 ≠ chart k1 → {'✓' if dollar_k1 != chart_k1 else '❌ FAILED'}")
    
    if dollar_k1 == chart_k1:
        print("\n  ❌ CRITICAL: Dollar and chart have SAME k1! Phonetic families are leaking!")
    else:
        print("\n  ✓ Phonetic validation passed")
    
except Exception as e:
    print(f"❌ Phonetics module error: {e}\n")
    import traceback
    traceback.print_exc()

# Test 3: Search Function
print("\n[TEST 3] Search Function - Basic Query")
try:
    from rhyme_core.search import search_all_categories
    
    # Test simple word
    test_word = "double"
    print(f"  Testing search for '{test_word}'...")
    
    result = search_all_categories(test_word, max_items=5)
    
    print(f"\n  Results structure:")
    for bucket in ['uncommon', 'slant', 'multiword', 'rap_targets']:
        count = len(result.get(bucket, []))
        print(f"    {bucket:15} : {count} results")
    
    print(f"\n  Sample results from 'uncommon' bucket:")
    for i, item in enumerate(result.get('uncommon', [])[:5], 1):
        word = item.get('word', 'N/A')
        print(f"    {i}. {word}")
    
    # Check for weird results
    all_words = []
    for bucket in ['uncommon', 'slant', 'multiword']:
        for item in result.get(bucket, []):
            all_words.append(item.get('word', ''))
    
    # Check for apostrophes in weird places
    weird_words = [w for w in all_words if "'" in w and " '" in w]
    if weird_words:
        print(f"\n  ⚠️ Found {len(weird_words)} words with weird apostrophes:")
        for w in weird_words[:10]:
            print(f"    - '{w}'")
    
    # Check if all results are identical
    if len(set(all_words)) < len(all_words) // 2:
        print(f"\n  ⚠️ Results have many duplicates or similar pattern")
    
except Exception as e:
    print(f"❌ Search function error: {e}\n")
    import traceback
    traceback.print_exc()

# Test 4: Database K-Key Integrity
print("\n[TEST 4] Database K-Key Integrity")
try:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # Check if k1/k2/k3 columns have data
    cur.execute("SELECT word, k1, k2, k3 FROM words WHERE word IN ('dollar', 'collar', 'chart', 'dart')")
    rows = cur.fetchall()
    
    print("  K-keys in database:")
    for word, k1, k2, k3 in rows:
        print(f"    {word:10} k1={k1:10} k2={k2[:20]:20} k3={k3[:20]:20}")
    
    # Check dollar vs chart
    dollar_row = [r for r in rows if r[0] == 'dollar']
    chart_row = [r for r in rows if r[0] == 'chart']
    
    if dollar_row and chart_row:
        dollar_k1_db = dollar_row[0][1]
        chart_k1_db = chart_row[0][1]
        
        if dollar_k1_db == chart_k1_db:
            print(f"\n  ❌ CRITICAL: In database, dollar k1='{dollar_k1_db}' == chart k1='{chart_k1_db}'")
            print(f"     Your database K-keys are WRONG! Need to rebuild database with fixed phonetics.py")
        else:
            print(f"\n  ✓ Database K-keys are correct (dollar k1='{dollar_k1_db}' ≠ chart k1='{chart_k1_db}')")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Database k-key check error: {e}\n")

# Test 5: Check for Weird Words in Database
print("\n[TEST 5] Check for Corrupted Database Entries")
try:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # Look for words with apostrophes followed by spaces
    cur.execute("SELECT word FROM words WHERE word LIKE \"% '%\" LIMIT 10")
    weird = cur.fetchall()
    
    if weird:
        print(f"  ⚠️ Found {len(weird)} words with pattern \" '\":")
        for (word,) in weird:
            print(f"    - '{word}'")
        print("\n  These might be the 'a. 'm' type results you're seeing!")
    else:
        print("  ✓ No obviously corrupted entries found")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Corruption check error: {e}\n")

print("\n" + "=" * 70)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 70)
print("\nLikely issues to investigate:")
print("1. Check if database K-keys were generated with old/broken phonetics.py")
print("2. Look for corrupted word entries in database (apostrophe issues)")
print("3. Verify search_all_categories() is actually querying database correctly")
print("4. Check if search is returning empty results and showing fallback data")
print("\nNext step: Run 'python tests/diagnose_search.py' and share the output!")
print("=" * 70)
