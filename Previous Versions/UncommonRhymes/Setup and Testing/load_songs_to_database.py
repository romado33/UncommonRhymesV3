#!/usr/bin/env python3
"""
FIXED Script to Load Songs into RhymeRarity Pattern Database
Corrected filenames and improved pattern extraction
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import our enhanced system
try:
    from enhanced_songs_pattern_database import EnhancedSongsPatternDatabase
    print("✅ Enhanced database system loaded successfully")
except ImportError as e:
    print(f"❌ Error importing database system: {e}")
    print("Make sure enhanced_songs_pattern_database.py is in the same directory")
    sys.exit(1)

def main():
    """Main execution function to process CSV files and create database"""
    
    print("🎵 RhymeRarity Songs Pattern Database Creator")
    print("=" * 60)
    
    # Initialize the enhanced processor
    print("🔧 Initializing enhanced database processor...")
    processor = EnhancedSongsPatternDatabase()
    
    # Define your CSV files with correct Windows paths
    # HIGHEST PRIORITY: Line-pair format (proven success format)
    csv_files = [
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part0.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part1.csv', 
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part2.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part3.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part4.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part5.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\updated_rappers_part6.csv',
        
        # HIGH PRIORITY: Individual artist CSV files (single-song format)
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\ArianaGrande.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Drake.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Eminem.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\TaylorSwift.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Beyonce.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\CardiB.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\BillieEilish.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\EdSheeran.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\JustinBieber.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\LadyGaga.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Rihanna.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\NickiMinaj.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\PostMalone.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\BTS.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\CharliePuth.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\ColdPlay.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\DuaLipa.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\KatyPerry.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Khalid.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\Maroon5.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\SelenaGomez.csv',
        
        # POETRY: High-quality poetry patterns
        r'C:\Users\RobDods\Apps\UncommonRhymes\PoetryCSV\PoetryFoundationData.csv',
        
        # MEDIUM PRIORITY: Large lyrics-data files (multi-row format) - Starting with smaller batch
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_1.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_2.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_3.csv',
        # Note: lyrics-data files are ~28MB each - you can add more later if needed:
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_4.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_5.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_6.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_7.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_8.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_9.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_10.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_11.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_12.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_13.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_14.csv',
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\lyrics-data_15.csv',
        
        # FALLBACK PRIORITY: Musical/theatrical format
        r'C:\Users\RobDods\Apps\UncommonRhymes\SongCSV\ham_lyrics.csv'
    ]
    
    # Check which files exist
    print(f"\n📂 Checking CSV files...")
    existing_files = []
    total_size_mb = 0
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            size_mb = os.path.getsize(csv_file) / (1024 * 1024)
            total_size_mb += size_mb
            print(f"   ✅ {os.path.basename(csv_file)} ({size_mb:.1f} MB)")
            existing_files.append(csv_file)
        else:
            print(f"   ❌ {os.path.basename(csv_file)} (not found)")
    
    if not existing_files:
        print("\n❌ No CSV files found! Please check file paths.")
        return
    
    print(f"\n🚀 Processing {len(existing_files)} CSV files (Total: {total_size_mb:.1f} MB)...")
    print("🔍 DEBUGGING MODE: Processing fewer files to identify issues")
    
    # Create the unified database with enhanced error handling
    try:
        db_path = processor.create_unified_songs_database(
            csv_files=existing_files,
            db_name="songs_patterns_unified_debug.db"
        )
        
        print(f"\n🎉 SUCCESS! Songs database created:")
        print(f"   📄 Database: {db_path}")
        
        # Show database info
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total patterns
        cursor.execute("SELECT COUNT(*) FROM song_rhyme_patterns")
        total_patterns = cursor.fetchone()[0]
        
        if total_patterns > 0:
            # Get unique artists
            cursor.execute("SELECT COUNT(DISTINCT artist) FROM song_rhyme_patterns")
            total_artists = cursor.fetchone()[0]
            
            # Get unique songs
            cursor.execute("SELECT COUNT(DISTINCT song_title) FROM song_rhyme_patterns")
            total_songs = cursor.fetchone()[0]
            
            # Show sample patterns
            cursor.execute("SELECT pattern, artist, song_title, line_distance FROM song_rhyme_patterns LIMIT 10")
            sample_patterns = cursor.fetchall()
            
            print(f"\n📊 DATABASE STATISTICS:")
            print(f"   🎯 Total patterns: {total_patterns:,}")
            print(f"   👨‍🎤 Unique artists: {total_artists:,}")
            print(f"   🎵 Unique songs: {total_songs:,}")
            
            print(f"\n🔍 SAMPLE PATTERNS:")
            for pattern, artist, song, distance in sample_patterns:
                print(f"   • '{pattern}' by {artist} - {song} (distance: {distance})")
                
        else:
            print(f"\n⚠️  WARNING: 0 patterns extracted!")
            print(f"This indicates an issue with pattern extraction logic.")
            print(f"Let's debug the CSV format detection and processing.")
            
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
