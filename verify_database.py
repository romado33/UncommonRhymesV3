#!/usr/bin/env python3
"""
Quick verification script for CMU Dictionary Database
Run this in your app directory to verify the database is set up correctly
"""

import sqlite3
import os
import sys

def verify_database(db_path='cmudict.db'):
    """Verify CMU dictionary database setup"""
    
    print("=" * 70)
    print("CMU DICTIONARY DATABASE VERIFICATION")
    print("=" * 70)
    print()
    
    # Check if database exists
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📊 Looking for database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"\n❌ ERROR: Database '{db_path}' not found!")
        print(f"\n💡 Solutions:")
        print(f"   1. Make sure cmudict.db is in this directory")
        print(f"   2. Or specify the correct path as: python verify_db.py <path_to_db>")
        return False
    
    print(f"✅ Database file found ({os.path.getsize(db_path) / 1024 / 1024:.2f} MB)")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for words table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words';")
        if not cursor.fetchone():
            print("❌ ERROR: 'words' table not found in database!")
            conn.close()
            return False
        
        print("✅ 'words' table exists")
        
        # Get table statistics
        cursor.execute("SELECT COUNT(*) FROM words")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT word) FROM words")
        unique_words = cursor.fetchone()[0]
        
        print(f"✅ Total entries: {total_count:,}")
        print(f"✅ Unique words: {unique_words:,}")
        print()
        
        # Test critical words
        print("🧪 Testing pronunciation lookups:")
        print("-" * 70)
        
        test_words = [
            ('guitar', 'G IH'),
            ('dog', 'D AO'),
            ('dollar', 'D AA1 L ER'),
            ('collar', 'K AA1 L ER'),
            ('art', 'AA1 R T'),
            ('cart', 'K AA1 R T'),
            ('heart', 'HH AA1 R T'),
            ('love', 'L AH1 V'),
            ('mind', 'M AY1 N D'),
            ('flow', 'F L OW')
        ]
        
        all_passed = True
        for word, expected_pattern in test_words:
            cursor.execute("SELECT word, pron FROM words WHERE word = ? LIMIT 1", (word,))
            result = cursor.fetchone()
            
            if result:
                found_word, found_pron = result
                # Check if phoneme pattern matches
                if any(p in found_pron for p in expected_pattern.split()[:2]):
                    print(f"   ✅ {word:12} -> {found_pron}")
                else:
                    print(f"   ⚠️  {word:12} -> {found_pron} (unexpected pattern)")
                    all_passed = False
            else:
                print(f"   ❌ {word:12} -> NOT FOUND")
                all_passed = False
        
        print()
        print("-" * 70)
        
        # Test the dollar/ART fix
        print("\n🔬 Testing Dollar/ART Issue Fix:")
        print("-" * 70)
        
        cursor.execute("SELECT word, pron FROM words WHERE word = 'dollar'")
        dollar_pron = cursor.fetchone()[1]
        
        cursor.execute("SELECT word, pron FROM words WHERE word = 'art'")
        art_pron = cursor.fetchone()[1]
        
        print(f"   dollar: {dollar_pron}")
        print(f"   art:    {art_pron}")
        
        # These should be in different families
        if 'L ER' in dollar_pron and 'R T' in art_pron:
            print(f"   ✅ Phonetic families correctly separated")
        else:
            print(f"   ⚠️  Phonetic separation may need review")
        
        conn.close()
        
        print()
        print("=" * 70)
        if all_passed:
            print("✅ DATABASE VERIFICATION PASSED!")
            print("\nYour database is ready to use with engine.py")
        else:
            print("⚠️  DATABASE VERIFICATION COMPLETED WITH WARNINGS")
            print("\nThe database works but some patterns may need review")
        print("=" * 70)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def check_engine_integration():
    """Check if engine.py exists and can be analyzed"""
    print("\n" + "=" * 70)
    print("ENGINE.PY INTEGRATION CHECK")
    print("=" * 70)
    print()
    
    engine_paths = [
        'engine.py',
        'rhyme_core/engine.py',
        'rhyme_core\\engine.py',
        'core/engine.py'
    ]
    
    found_engine = False
    for path in engine_paths:
        if os.path.exists(path):
            print(f"✅ Found engine.py at: {path}")
            found_engine = True
            
            # Try to read and check for database connection
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if 'sqlite3.connect' in content:
                    print(f"✅ Database connection code found")
                    
                    # Look for database file name
                    import re
                    db_patterns = [
                        r'sqlite3\.connect\(["\']([^"\']+)["\']',
                        r'DB_PATH\s*=\s*["\']([^"\']+)["\']',
                        r'db_path\s*=\s*["\']([^"\']+)["\']'
                    ]
                    
                    for pattern in db_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"📊 Database file(s) referenced: {', '.join(set(matches))}")
                            if 'cmudict.db' in matches:
                                print(f"   ✅ Already configured for cmudict.db!")
                            else:
                                print(f"   💡 You may need to update to 'cmudict.db'")
                            break
                else:
                    print(f"⚠️  No database connection found in engine.py")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze engine.py: {e}")
            
            break
    
    if not found_engine:
        print(f"⚠️  engine.py not found in common locations")
        print(f"   Checked: {', '.join(engine_paths)}")
    
    print()

if __name__ == "__main__":
    # Allow custom database path as argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'cmudict.db'
    
    # Run verification
    success = verify_database(db_path)
    
    # Check engine integration
    check_engine_integration()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
