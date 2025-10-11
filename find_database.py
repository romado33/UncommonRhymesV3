#!/usr/bin/env python3
"""
Find your words.db database file - Windows compatible
Run this from your project root: python find_database.py
"""
import os
from pathlib import Path

print("🔍 Searching for words.db database file...\n")

# Get current directory
current_dir = Path.cwd()
print(f"Current directory: {current_dir}\n")

# Search common locations relative to project root
search_locations = [
    current_dir / "data" / "words.db",
    current_dir / "data" / "cmudict.db",
    current_dir / "rhyme_core" / "data" / "words.db",
    current_dir / "rhyme_core" / "data" / "cmudict.db",
    current_dir.parent / "data" / "words.db",
]

found_files = []

print("📂 Checking standard locations:")
for location in search_locations:
    print(f"   Checking: {location}")
    if location.exists() and location.is_file():
        size_mb = location.stat().st_size / (1024 * 1024)
        found_files.append((location, size_mb))
        print(f"   ✅ FOUND! Size: {size_mb:.1f} MB\n")

# Also search recursively for any .db files
print("\n🔎 Searching recursively for all .db files...")
try:
    for root, dirs, files in os.walk(current_dir):
        # Skip common directories to avoid
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.db'):
                file_path = Path(root) / file
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    # Only show databases that are likely the words database (>5MB)
                    if size_mb > 5:
                        found_files.append((file_path, size_mb))
                        print(f"   ✅ Found: {file_path.name}")
                        print(f"      Location: {file_path}")
                        print(f"      Size: {size_mb:.1f} MB\n")
                except:
                    pass
except Exception as e:
    print(f"   Error during search: {e}")

# Results
print("\n" + "="*80)
if not found_files:
    print("❌ No database files found in project directory!")
    print("\n💡 Possible reasons:")
    print("   1. Database hasn't been created yet")
    print("   2. Database is in a different location")
    print("   3. You need to download/build the database first")
    print("\n📋 Expected locations:")
    print("   - data/words.db")
    print("   - rhyme_core/data/words.db")
    print("   - data/cmudict.db")
    print("\n🔧 Next steps:")
    print("   1. Check if you have a database file anywhere")
    print("   2. Look for database build/setup scripts")
    print("   3. Check project documentation for database setup")
else:
    print(f"✅ Found {len(found_files)} potential database file(s)\n")
    
    # Find the largest (most likely to be the main database)
    largest = max(found_files, key=lambda x: x[1])
    
    print("💡 RECOMMENDED: Use this database file:")
    print(f"   File: {largest[0].name}")
    print(f"   Path: {largest[0]}")
    print(f"   Size: {largest[1]:.1f} MB")
    
    print("\n🚀 To run the migration, use this command:")
    print(f'\n   python database_migration.py --db "{largest[0]}" --backup')
    
    # Show all found files
    if len(found_files) > 1:
        print(f"\n📋 All found database files:")
        for db_path, size in sorted(found_files, key=lambda x: x[1], reverse=True):
            print(f"   - {db_path.name} ({size:.1f} MB): {db_path}")

print("="*80)
