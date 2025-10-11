#!/usr/bin/env python3
"""
Quick check: Is the fixed search.py installed?
"""

import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\RobDods\apps\uncommonrhymesv3")

print("=" * 70)
print("🔍 CHECKING INSTALLED SEARCH.PY VERSION")
print("=" * 70)

# Check 1: Which file is being imported?
print("\n1️⃣ Checking import location...")
try:
    import rhyme_core.search as search_module
    print(f"   ✅ Imported from: {search_module.__file__}")
except ImportError as e:
    print(f"   ❌ Cannot import: {e}")
    sys.exit(1)

# Check 2: Does it have the new functions?
print("\n2️⃣ Checking for new functions in fixed version...")

has_validation = hasattr(search_module, '_is_valid_phoneme_list')
has_db_fallback = hasattr(search_module, '_get_pronunciation_from_db')
has_parse_helper = hasattr(search_module, '_parse_pron_string')

print(f"   _is_valid_phoneme_list: {'✅ Found' if has_validation else '❌ Missing'}")
print(f"   _get_pronunciation_from_db: {'✅ Found' if has_db_fallback else '❌ Missing'}")
print(f"   _parse_pron_string: {'✅ Found' if has_parse_helper else '❌ Missing'}")

if has_validation and has_db_fallback and has_parse_helper:
    print("\n   ✅ FIXED VERSION IS INSTALLED!")
else:
    print("\n   ❌ OLD VERSION STILL INSTALLED!")
    print("\n   Action needed:")
    print("   1. Copy search_FIXED_FINAL.py to rhyme_core/search.py")
    print("   2. Clear Python cache:")
    print("      Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force")
    print("   3. Restart Python")

# Check 3: Test the validation function
if has_validation:
    print("\n3️⃣ Testing validation function...")
    try:
        result1 = search_module._is_valid_phoneme_list(['double'])
        result2 = search_module._is_valid_phoneme_list(['D', 'AH1', 'B', 'AH0', 'L'])
        
        print(f"   ['double'] → {result1} {'✅ (correct)' if not result1 else '❌ (should be False)'}")
        print(f"   ['D', 'AH1', ...] → {result2} {'✅ (correct)' if result2 else '❌ (should be True)'}")
    except Exception as e:
        print(f"   ❌ Error testing: {e}")

# Check 4: Test the database fallback
if has_db_fallback:
    print("\n4️⃣ Testing database fallback...")
    try:
        result = search_module._get_pronunciation_from_db('double')
        if result:
            print(f"   ✅ Found pronunciation: {result}")
        else:
            print(f"   ⚠️  Returned None - database might not have 'double'")
    except Exception as e:
        print(f"   ❌ Error testing: {e}")
        import traceback
        traceback.print_exc()

# Check 5: Check for apostrophe filter in source
print("\n5️⃣ Checking for apostrophe filter in code...")
try:
    import inspect
    source = inspect.getsource(search_module._query_words)
    
    if '%\'%' in source or "\"%'%\"" in source:
        print(f"   ✅ Apostrophe filter found in _query_words")
    else:
        print(f"   ⚠️  Apostrophe filter might be missing")
except Exception as e:
    print(f"   ⚠️  Could not check source: {e}")

print("\n" + "=" * 70)
print("📋 SUMMARY")
print("=" * 70)

if has_validation and has_db_fallback and has_parse_helper:
    print("✅ Fixed version is installed")
    print("🔍 If still getting errors, run deep_diagnostic.py for detailed trace")
else:
    print("❌ Old version still installed - follow installation steps!")

print("=" * 70)
