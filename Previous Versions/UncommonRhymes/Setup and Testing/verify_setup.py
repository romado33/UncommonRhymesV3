#!/usr/bin/env python3
"""
RhymeRarity Environment Verification Script
Run this first to check if your environment is ready
"""

import os
import sys
import sqlite3
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 7:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python 3.7+ required")
        return False

def check_required_modules():
    """Check if required Python modules are available"""
    required_modules = ['pandas', 'sqlite3', 'hashlib', 'difflib', 'unicodedata']
    optional_modules = ['Levenshtein']
    
    print(f"\n📦 Required Modules:")
    all_required_available = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - Install with: pip install {module}")
            all_required_available = False
    
    print(f"\n🔧 Optional Modules (for better performance):")
    for module in optional_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ⚠️  {module} - Install with: pip install python-Levenshtein")
    
    return all_required_available

def check_rhyme_files():
    """Check if RhymeRarity Python files are present"""
    required_files = [
        'cross_file_deduplicator.py',
        'enhanced_songs_pattern_database.py',
        'load_songs_to_database.py', 
        'query_songs_database.py'
    ]
    
    print(f"\n📄 RhymeRarity System Files:")
    all_files_present = True
    
    for file in required_files:
        if os.path.exists(file):
            size_kb = os.path.getsize(file) / 1024
            print(f"   ✅ {file} ({size_kb:.1f} KB)")
        else:
            print(f"   ❌ {file} - Missing!")
            all_files_present = False
    
    return all_files_present

def check_csv_files():
    """Check for CSV data files"""
    common_csv_locations = [
        # Current directory
        'updated_rappers_part0__1_.csv',
        'ArianaGrande.csv', 
        'lyrics-data_1.csv',
        'combined_lyrics.csv',
        'ham_lyrics.csv',
        # Subdirectories
        'csv-data/updated_rappers_part0__1_.csv',
        'data/updated_rappers_part0__1_.csv',
        # Uploaded files directory 
        '/mnt/user-data/uploads/updated_rappers_part0__1_.csv',
        '/mnt/user-data/uploads/ArianaGrande.csv',
        '/mnt/user-data/uploads/lyrics-data_1.csv',
        '/mnt/user-data/uploads/combined_lyrics.csv',
        '/mnt/user-data/uploads/ham_lyrics.csv'
    ]
    
    print(f"\n📊 CSV Data Files:")
    found_files = []
    
    for csv_file in common_csv_locations:
        if os.path.exists(csv_file):
            size_mb = os.path.getsize(csv_file) / (1024 * 1024)
            print(f"   ✅ {csv_file} ({size_mb:.1f} MB)")
            found_files.append(csv_file)
    
    if not found_files:
        print("   ⚠️  No CSV files found in common locations")
        print("   💡 Make sure your CSV files are in the project directory")
        print("      or update paths in load_songs_to_database.py")
    
    return found_files

def check_existing_database():
    """Check if database already exists"""
    db_files = ['songs_patterns_unified.db', 'rhyme_patterns.db']
    
    print(f"\n💾 Existing Databases:")
    found_dbs = []
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size_mb = os.path.getsize(db_file) / (1024 * 1024)
            
            # Try to connect and get basic info
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                print(f"   ✅ {db_file} ({size_mb:.1f} MB)")
                print(f"      Tables: {[t[0] for t in tables]}")
                found_dbs.append(db_file)
                
            except sqlite3.Error:
                print(f"   ⚠️  {db_file} ({size_mb:.1f} MB) - Corrupted?")
    
    if not found_dbs:
        print("   ℹ️  No existing databases found (this is normal for first run)")
    
    return found_dbs

def main():
    """Main verification function"""
    print("🎵 RhymeRarity Environment Verification")
    print("=" * 60)
    
    # Run all checks
    python_ok = check_python_version()
    modules_ok = check_required_modules()
    files_ok = check_rhyme_files()
    csv_files = check_csv_files()
    existing_dbs = check_existing_database()
    
    print(f"\n" + "=" * 60)
    print(f"📋 VERIFICATION SUMMARY")
    print(f"=" * 60)
    
    if python_ok and modules_ok and files_ok:
        print(f"🎉 Environment Ready!")
        print(f"   ✅ Python compatibility: OK")
        print(f"   ✅ Required modules: OK") 
        print(f"   ✅ RhymeRarity files: OK")
        
        if csv_files:
            print(f"   ✅ CSV data files: {len(csv_files)} found")
            print(f"\n🚀 NEXT STEPS:")
            print(f"   1. Run: python load_songs_to_database.py")
            print(f"   2. Wait for database creation to complete")
            print(f"   3. Test with: python query_songs_database.py")
        else:
            print(f"   ⚠️  CSV data files: None found")
            print(f"\n⚠️  ACTION NEEDED:")
            print(f"   1. Add CSV files to your project directory")
            print(f"   2. Or update file paths in load_songs_to_database.py")
            print(f"   3. Then run: python load_songs_to_database.py")
        
        if existing_dbs:
            print(f"\n💡 EXISTING DATABASES FOUND:")
            print(f"   You can test immediately with: python query_songs_database.py")
            
    else:
        print(f"❌ Environment Issues Found")
        if not python_ok:
            print(f"   🔧 Install Python 3.7+")
        if not modules_ok:
            print(f"   🔧 Install missing modules: pip install pandas")
        if not files_ok:
            print(f"   🔧 Ensure all RhymeRarity Python files are present")
        
        print(f"\n🔧 FIX ISSUES THEN RE-RUN THIS SCRIPT")
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    main()
