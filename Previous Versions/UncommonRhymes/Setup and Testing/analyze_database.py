#!/usr/bin/env python3
"""
Database Analysis Script - Get comprehensive statistics from your patterns database
Run this locally and share the output with Claude for analysis
"""

import sqlite3
import os

def analyze_patterns_database(db_path="songs_patterns_unified.db"):
    """Analyze the patterns database and generate comprehensive statistics"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🎵 RHYME RARITY DATABASE ANALYSIS")
        print("=" * 60)
        
        # Basic database info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables: {[t[0] for t in tables]}")
        
        # Get the main table name
        main_table = "song_rhyme_patterns" if ("song_rhyme_patterns",) in tables else tables[0][0]
        
        # Database size
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"💾 Database size: {db_size_mb:.1f} MB")
        
        # Total patterns
        cursor.execute(f"SELECT COUNT(*) FROM {main_table}")
        total_patterns = cursor.fetchone()[0]
        print(f"🎯 Total patterns: {total_patterns:,}")
        
        # Unique artists
        cursor.execute(f"SELECT COUNT(DISTINCT artist) FROM {main_table}")
        total_artists = cursor.fetchone()[0]
        print(f"👨‍🎤 Unique artists: {total_artists:,}")
        
        # Unique songs
        cursor.execute(f"SELECT COUNT(DISTINCT song_title) FROM {main_table}")
        total_songs = cursor.fetchone()[0]
        print(f"🎵 Unique songs: {total_songs:,}")
        
        # Genre breakdown
        print(f"\n🎼 GENRE DISTRIBUTION:")
        cursor.execute(f"SELECT genre, COUNT(*) FROM {main_table} GROUP BY genre ORDER BY COUNT(*) DESC")
        genres = cursor.fetchall()
        for genre, count in genres:
            percentage = (count / total_patterns) * 100
            print(f"   • {genre}: {count:,} ({percentage:.1f}%)")
        
        # Top artists by pattern count
        print(f"\n👑 TOP ARTISTS BY PATTERNS:")
        cursor.execute(f"SELECT artist, COUNT(*) FROM {main_table} GROUP BY artist ORDER BY COUNT(*) DESC LIMIT 10")
        top_artists = cursor.fetchall()
        for artist, count in top_artists:
            print(f"   • {artist}: {count:,} patterns")
        
        # Pattern types
        print(f"\n📝 PATTERN TYPES:")
        cursor.execute(f"SELECT pattern_type, COUNT(*) FROM {main_table} GROUP BY pattern_type ORDER BY COUNT(*) DESC")
        pattern_types = cursor.fetchall()
        for ptype, count in pattern_types:
            print(f"   • {ptype}: {count:,}")
        
        # Line distance distribution
        print(f"\n📏 LINE DISTANCE DISTRIBUTION:")
        cursor.execute(f"SELECT line_distance, COUNT(*) FROM {main_table} GROUP BY line_distance ORDER BY line_distance")
        distances = cursor.fetchall()
        for distance, count in distances:
            print(f"   • {distance} line{'s' if distance > 1 else ''} apart: {count:,}")
        
        # Confidence score distribution
        print(f"\n📊 CONFIDENCE SCORE DISTRIBUTION:")
        cursor.execute(f"SELECT ROUND(confidence_score, 1) as conf, COUNT(*) FROM {main_table} GROUP BY ROUND(confidence_score, 1) ORDER BY conf DESC")
        confidence_dist = cursor.fetchall()[:10]  # Top 10
        for conf, count in confidence_dist:
            print(f"   • {conf}: {count:,} patterns")
        
        # Sample high-quality patterns
        print(f"\n⭐ SAMPLE HIGH-QUALITY PATTERNS:")
        cursor.execute(f"""
            SELECT pattern, artist, song_title, confidence_score, line_distance 
            FROM {main_table} 
            WHERE confidence_score >= 0.8 
            ORDER BY confidence_score DESC 
            LIMIT 20
        """)
        samples = cursor.fetchall()
        for pattern, artist, song, conf, dist in samples:
            print(f"   • '{pattern}' - {artist} ({conf:.2f}, dist={dist})")
        
        # Most common target words
        print(f"\n🎯 MOST COMMON TARGET RHYME WORDS:")
        cursor.execute(f"SELECT target_word, COUNT(*) FROM {main_table} GROUP BY target_word ORDER BY COUNT(*) DESC LIMIT 15")
        target_words = cursor.fetchall()
        for word, count in target_words:
            print(f"   • {word}: {count:,} patterns")
        
        # Source file analysis
        if total_patterns > 0:
            print(f"\n📁 SOURCE FILE BREAKDOWN:")
            cursor.execute(f"SELECT source_file, COUNT(*) FROM {main_table} GROUP BY source_file ORDER BY COUNT(*) DESC")
            source_files = cursor.fetchall()
            for source, count in source_files:
                if source:
                    percentage = (count / total_patterns) * 100
                    print(f"   • {source}: {count:,} ({percentage:.1f}%)")
        
        # Quality metrics
        cursor.execute(f"SELECT AVG(confidence_score), MIN(confidence_score), MAX(confidence_score) FROM {main_table}")
        avg_conf, min_conf, max_conf = cursor.fetchone()
        print(f"\n📈 QUALITY METRICS:")
        print(f"   • Average confidence: {avg_conf:.3f}")
        print(f"   • Min confidence: {min_conf:.3f}")
        print(f"   • Max confidence: {max_conf:.3f}")
        
        # Potential duplicate check
        cursor.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT pattern, artist, song_title, COUNT(*) 
                FROM {main_table} 
                GROUP BY pattern, artist, song_title 
                HAVING COUNT(*) > 1
            )
        """)
        duplicates = cursor.fetchone()[0]
        print(f"   • Potential duplicates: {duplicates:,}")
        
        conn.close()
        
        print(f"\n✅ Analysis complete! Share this output with Claude for detailed insights.")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Try different possible database names
    db_candidates = [
        "songs_patterns_unified.db",
        "songs_patterns_unified_debug.db", 
        "rhyme_patterns.db",
        "patterns.db"
    ]
    
    found_db = None
    for db in db_candidates:
        if os.path.exists(db):
            found_db = db
            break
    
    if found_db:
        print(f"📁 Found database: {found_db}")
        analyze_patterns_database(found_db)
    else:
        print("❌ No database files found. Please run load_songs_to_database.py first.")
        print("Looking for: " + ", ".join(db_candidates))
