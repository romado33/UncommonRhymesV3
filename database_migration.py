#!/usr/bin/env python3
"""
Database Migration Script - Add K3 Support
Adds k3 column and indexes to existing RhymeRarity database

WHAT THIS DOES:
1. Checks if k3 column exists
2. If missing, adds k3 column to words table
3. Populates k3 from existing pronunciations
4. Creates indexes on k1, k2, k3 for performance
5. Validates the migration

REQUIREMENTS:
- Existing words table with columns: word, pron, k1, k2
- phonetics.py module with k_keys() function

USAGE:
    python database_migration.py --db path/to/words.db

WARNING: This will modify your database. Back up first!
"""

import sys
import sqlite3
import time
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from rhyme_core.phonetics import parse_pron, k_keys
    print("✅ Successfully imported phonetics module")
except ImportError:
    print("❌ Failed to import phonetics module")
    print("   Make sure phonetics.py is in rhyme_core/")
    sys.exit(1)

# =============================================================================
# DATABASE INSPECTION
# =============================================================================

def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if table exists in database"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def check_column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check if column exists in table"""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def check_index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    """Check if index exists in database"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None

# =============================================================================
# MIGRATION STEPS
# =============================================================================

def step1_add_k3_column(conn: sqlite3.Connection) -> bool:
    """
    Step 1: Add k3 column to words table
    
    Returns True if column was added or already exists
    """
    print("\n" + "=" * 80)
    print("STEP 1: Add K3 Column")
    print("=" * 80)
    
    # Check if column already exists
    if check_column_exists(conn, "words", "k3"):
        print("✅ k3 column already exists - skipping")
        return True
    
    try:
        print("⏳ Adding k3 column to words table...")
        conn.execute("ALTER TABLE words ADD COLUMN k3 TEXT")
        conn.commit()
        print("✅ k3 column added successfully")
        return True
    except sqlite3.Error as e:
        print(f"❌ Failed to add k3 column: {e}")
        return False

def step2_populate_k3(conn: sqlite3.Connection) -> bool:
    """
    Step 2: Populate k3 values from existing pronunciations
    
    For each word, extract k3 from pronunciation using k_keys() function
    """
    print("\n" + "=" * 80)
    print("STEP 2: Populate K3 Values")
    print("=" * 80)
    
    try:
        # Get all words with pronunciations
        cursor = conn.execute("SELECT word, pron FROM words WHERE pron IS NOT NULL AND pron != ''")
        rows = cursor.fetchall()
        
        total = len(rows)
        print(f"⏳ Processing {total:,} words...")
        
        updated = 0
        errors = 0
        
        start_time = time.time()
        
        for i, (word, pron) in enumerate(rows):
            try:
                # Parse pronunciation and extract keys
                phones = parse_pron(pron)
                if not phones:
                    errors += 1
                    continue
                
                keys = k_keys(phones)
                if not keys or len(keys) < 3:
                    errors += 1
                    continue
                
                k3 = keys[2]  # Third element is k3
                
                # Update database
                conn.execute("UPDATE words SET k3 = ? WHERE word = ?", (k3, word))
                updated += 1
                
            except Exception as word_error:
                # Handle individual word processing errors
                errors += 1
                if errors <= 10:  # Only print first 10 errors to avoid spam
                    print(f"   ⚠️  Error processing '{word}': {word_error}")
            
            # Progress indicator (outside try block so it always runs)
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (total - i - 1) / rate if rate > 0 else 0
                print(f"   Progress: {i+1:,}/{total:,} ({(i+1)/total*100:.1f}%) - "
                      f"{rate:.0f} words/sec - "
                      f"ETA: {remaining:.0f}s")
        
        conn.commit()
        
        elapsed = time.time() - start_time
        print(f"\n✅ k3 population completed in {elapsed:.1f}s")
        print(f"   Updated: {updated:,} words")
        print(f"   Errors: {errors:,} words")
        print(f"   Rate: {updated/elapsed:.0f} words/sec")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to populate k3: {e}")
        conn.rollback()
        return False

def step3_create_indexes(conn: sqlite3.Connection) -> bool:
    """
    Step 3: Create indexes on k1, k2, k3 for query performance
    
    Indexes are critical for fast lookups in the three-stage query architecture
    """
    print("\n" + "=" * 80)
    print("STEP 3: Create Indexes")
    print("=" * 80)
    
    indexes = [
        ("idx_k1", "k1"),
        ("idx_k2", "k2"),
        ("idx_k3", "k3"),
    ]
    
    success = True
    
    for index_name, column_name in indexes:
        try:
            # Check if index already exists
            if check_index_exists(conn, index_name):
                print(f"✅ {index_name} already exists - skipping")
                continue
            
            print(f"⏳ Creating index {index_name} on {column_name}...")
            start_time = time.time()
            
            conn.execute(f"CREATE INDEX {index_name} ON words({column_name})")
            conn.commit()
            
            elapsed = time.time() - start_time
            print(f"✅ {index_name} created in {elapsed:.1f}s")
            
        except sqlite3.Error as e:
            print(f"❌ Failed to create {index_name}: {e}")
            success = False
    
    return success

def step4_validate_migration(conn: sqlite3.Connection) -> bool:
    """
    Step 4: Validate migration completed successfully
    
    Checks:
    1. k3 column exists
    2. k3 values are populated (non-null for most words)
    3. Indexes exist
    4. Test queries work
    """
    print("\n" + "=" * 80)
    print("STEP 4: Validate Migration")
    print("=" * 80)
    
    all_checks_passed = True
    
    # Check 1: k3 column exists
    print("\n📋 Check 1: k3 column exists")
    if check_column_exists(conn, "words", "k3"):
        print("✅ k3 column exists")
    else:
        print("❌ k3 column missing!")
        all_checks_passed = False
    
    # Check 2: k3 values populated
    print("\n📋 Check 2: k3 values populated")
    cursor = conn.execute("SELECT COUNT(*) FROM words WHERE k3 IS NOT NULL AND k3 != ''")
    k3_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM words")
    total_count = cursor.fetchone()[0]
    
    percentage = (k3_count / total_count * 100) if total_count > 0 else 0
    
    print(f"   k3 populated: {k3_count:,}/{total_count:,} ({percentage:.1f}%)")
    
    if percentage >= 95:
        print("✅ k3 values adequately populated")
    else:
        print(f"⚠️  Only {percentage:.1f}% of words have k3 values")
        all_checks_passed = False
    
    # Check 3: Indexes exist
    print("\n📋 Check 3: Indexes exist")
    for index_name in ["idx_k1", "idx_k2", "idx_k3"]:
        if check_index_exists(conn, index_name):
            print(f"✅ {index_name} exists")
        else:
            print(f"❌ {index_name} missing!")
            all_checks_passed = False
    
    # Check 4: Test queries
    print("\n📋 Check 4: Test queries")
    try:
        # Test k3 query
        cursor = conn.execute("SELECT COUNT(*) FROM words WHERE k3 = 'AA1|L ER0'")
        count = cursor.fetchone()[0]
        print(f"✅ k3 query works (found {count} words with k3='AA1|L ER0')")
        
        # Test that we can find dollar/collar family
        cursor = conn.execute("SELECT word FROM words WHERE k3 = 'AA1|L ER0' LIMIT 5")
        words = [row[0] for row in cursor.fetchall()]
        print(f"   Example words: {', '.join(words)}")
        
        if "dollar" in words or "collar" in words:
            print("✅ Dollar/collar family found correctly")
        else:
            print("⚠️  Dollar/collar not in results (may be due to limit)")
        
    except sqlite3.Error as e:
        print(f"❌ Test queries failed: {e}")
        all_checks_passed = False
    
    # Check 5: Verify dollar/ART separation
    print("\n📋 Check 5: Verify dollar/ART separation")
    try:
        # Get dollar's k3
        cursor = conn.execute("SELECT k3 FROM words WHERE word = 'dollar'")
        dollar_k3 = cursor.fetchone()
        
        # Get chart's k3
        cursor = conn.execute("SELECT k3 FROM words WHERE word = 'chart'")
        chart_k3 = cursor.fetchone()
        
        if dollar_k3 and chart_k3:
            dollar_k3 = dollar_k3[0]
            chart_k3 = chart_k3[0]
            
            print(f"   dollar k3: {dollar_k3}")
            print(f"   chart k3:  {chart_k3}")
            
            if dollar_k3 != chart_k3:
                print("✅ Dollar and chart have DIFFERENT k3 keys (bug fixed!)")
            else:
                print("❌ Dollar and chart have SAME k3 key (bug not fixed!)")
                all_checks_passed = False
        else:
            print("⚠️  Could not find dollar or chart in database")
    
    except sqlite3.Error as e:
        print(f"❌ Separation test failed: {e}")
        all_checks_passed = False
    
    return all_checks_passed

# =============================================================================
# MAIN MIGRATION
# =============================================================================

def run_migration(db_path: Path, dry_run: bool = False) -> bool:
    """
    Run complete migration process
    
    Args:
        db_path: Path to database file
        dry_run: If True, only check status without making changes
    
    Returns:
        True if migration successful
    """
    print("\n" + "=" * 80)
    print("RHYMERARITY DATABASE MIGRATION")
    print("Adding K3 support for enhanced phonetic matching")
    print("=" * 80)
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"\nDatabase: {db_path}")
    print(f"Size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        print("✅ Database connection established")
        
        # Check if words table exists
        if not check_table_exists(conn, "words"):
            print("❌ 'words' table not found in database")
            return False
        
        print("✅ 'words' table found")
        
        # Get table info
        cursor = conn.execute("SELECT COUNT(*) FROM words")
        word_count = cursor.fetchone()[0]
        print(f"   Total words: {word_count:,}")
        
        if dry_run:
            print("\n📊 Current Status:")
            
            # Check k3 column
            has_k3 = check_column_exists(conn, "words", "k3")
            print(f"   k3 column: {'✅ Exists' if has_k3 else '❌ Missing'}")
            
            if has_k3:
                cursor = conn.execute("SELECT COUNT(*) FROM words WHERE k3 IS NOT NULL")
                k3_count = cursor.fetchone()[0]
                print(f"   k3 populated: {k3_count:,}/{word_count:,} ({k3_count/word_count*100:.1f}%)")
            
            # Check indexes
            for index_name in ["idx_k1", "idx_k2", "idx_k3"]:
                has_index = check_index_exists(conn, index_name)
                print(f"   {index_name}: {'✅ Exists' if has_index else '❌ Missing'}")
            
            return True
        
        # Run migration steps
        start_time = time.time()
        
        success = True
        success = success and step1_add_k3_column(conn)
        success = success and step2_populate_k3(conn)
        success = success and step3_create_indexes(conn)
        
        if success:
            success = step4_validate_migration(conn)
        
        elapsed = time.time() - start_time
        
        # Summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        
        if success:
            print(f"✅ Migration completed successfully in {elapsed:.1f}s")
            print(f"\nNext steps:")
            print(f"1. Deploy search_FIXED.py to production")
            print(f"2. Run diagnostic_tests.py to validate")
            print(f"3. Run benchmark.py to measure recall improvement")
        else:
            print(f"❌ Migration failed after {elapsed:.1f}s")
            print(f"\nReview error messages above and:")
            print(f"1. Check database permissions")
            print(f"2. Verify phonetics.py is accessible")
            print(f"3. Ensure sufficient disk space")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"\n❌ Migration failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate RhymeRarity database to add K3 support"
    )
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to database file (e.g., data/words.db)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check status without making changes"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before migration (recommended)"
    )
    
    args = parser.parse_args()
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        import shutil
        backup_path = args.db.parent / f"{args.db.stem}_backup_{int(time.time())}.db"
        print(f"Creating backup: {backup_path}")
        shutil.copy2(args.db, backup_path)
        print(f"✅ Backup created")
    
    # Run migration
    success = run_migration(args.db, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)