#!/usr/bin/env python3
"""
Update k3 column in words_index.sqlite database.

This script populates the k3 column with stress-preserved rhyme keys.
Run this after updating phonetics.py with the new k_keys implementation.

Usage:
    python update_k3_column.py [path/to/words_index.sqlite]

If no path provided, tries common locations:
    - data/dev/words_index.sqlite
    - words_index.sqlite
"""

import sqlite3
import sys
from pathlib import Path
import time

# Try to import updated phonetics
try:
    from phonetics import k_keys, parse_pron
    print("✓ Using updated phonetics.py from current directory")
except ImportError:
    print("ERROR: Cannot import phonetics.py")
    print("Make sure phonetics_updated.py is renamed to phonetics.py in this directory")
    sys.exit(1)

def find_database():
    """Find the database file."""
    candidates = [
        Path("data/dev/words_index.sqlite"),
        Path("words_index.sqlite"),
        Path("../data/dev/words_index.sqlite"),
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None

def update_k3_column(db_path: Path, batch_size: int = 1000):
    """Update k3 column for all words in database."""
    print(f"\nOpening database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if k3 column exists
    cursor.execute("PRAGMA table_info(words)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'k3' not in columns:
        print("ERROR: k3 column doesn't exist in database")
        print("Available columns:", columns)
        conn.close()
        return False
    
    # Count total words
    cursor.execute("SELECT COUNT(*) FROM words")
    total_words = cursor.fetchone()[0]
    print(f"Total words in database: {total_words:,}")
    
    # Get all words and pronunciations
    print("\nFetching words...")
    cursor.execute("SELECT word, pron FROM words")
    all_words = cursor.fetchall()
    
    print(f"Processing {len(all_words):,} words...")
    
    # Process in batches
    updated = 0
    errors = 0
    start_time = time.time()
    
    for i in range(0, len(all_words), batch_size):
        batch = all_words[i:i+batch_size]
        
        for word, pron in batch:
            try:
                phones = parse_pron(pron)
                k1, k2, k3 = k_keys(phones)
                
                # Update k3 column
                cursor.execute("UPDATE words SET k3 = ? WHERE word = ?", (k3, word))
                updated += 1
                
            except Exception as e:
                print(f"  ERROR processing '{word}': {e}")
                errors += 1
        
        # Commit batch
        conn.commit()
        
        # Progress report
        progress = (i + len(batch)) / len(all_words) * 100
        elapsed = time.time() - start_time
        rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
        eta = (len(all_words) - (i + len(batch))) / rate if rate > 0 else 0
        
        print(f"  Progress: {progress:5.1f}% | {updated:,}/{len(all_words):,} | "
              f"{rate:,.0f} words/sec | ETA: {eta:.0f}s", end='\r')
    
    print()  # New line after progress
    
    # Final commit
    conn.commit()
    
    # Verify updates
    print("\nVerifying updates...")
    cursor.execute("SELECT COUNT(*) FROM words WHERE k3 IS NOT NULL AND k3 != ''")
    k3_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT word, pron, k1, k2, k3 FROM words LIMIT 5")
    print("\nSample updated records:")
    print("-" * 80)
    for word, pron, k1, k2, k3 in cursor.fetchall():
        print(f"{word:15} | k1='{k1:10}' | k2='{k2:20}' | k3='{k3:20}'")
    
    conn.close()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"✓ Update complete!")
    print(f"  Total words: {total_words:,}")
    print(f"  Updated: {updated:,}")
    print(f"  Errors: {errors:,}")
    print(f"  k3 populated: {k3_count:,}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Rate: {updated/elapsed:,.0f} words/sec")
    print("=" * 80)
    
    return True

def main():
    print("=" * 80)
    print("K3 Column Update Script")
    print("=" * 80)
    
    # Get database path
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = find_database()
    
    if not db_path:
        print("ERROR: Could not find database file")
        print("\nUsage:")
        print("  python update_k3_column.py [path/to/words_index.sqlite]")
        print("\nOr place database at one of these locations:")
        print("  - data/dev/words_index.sqlite")
        print("  - words_index.sqlite")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)
    
    # Backup warning
    print("\n⚠️  WARNING: This will modify your database!")
    print(f"   Database: {db_path.absolute()}")
    print("\n   Recommendation: Create a backup first:")
    print(f"   cp {db_path} {db_path}.backup")
    
    response = input("\nContinue? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    # Run update
    success = update_k3_column(db_path)
    
    if success:
        print("\n✓ Database updated successfully!")
        print("\nNext steps:")
        print("1. Test the updated database:")
        print("   python test_k_keys.py")
        print("2. Run your application:")
        print("   python app.py")
    else:
        print("\n✗ Update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
