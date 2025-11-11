#!/usr/bin/env python3
"""
Simple Rhyme Query Script for RhymeRarity Songs Database
Demonstrates how to search for target rhymes using your loaded songs database
"""

import sqlite3
import os

def search_target_rhymes(source_word, db_path="songs_patterns_unified.db", limit=20):
    """
    Search for target rhymes given a source word
    
    Args:
        source_word (str): The word to find rhymes for (e.g., "find")
        db_path (str): Path to the database
        limit (int): Maximum number of results to return
    
    Returns:
        List of rhyme matches with context
    """
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for target rhymes - no duplicates thanks to our deduplication system!
        query = """
        SELECT DISTINCT 
            target_word,
            artist,
            song_title,
            pattern,
            line_distance,
            confidence_score,
            source_context,
            target_context,
            cultural_significance
        FROM song_rhyme_patterns 
        WHERE source_word LIKE ? 
           OR pattern LIKE ?
        ORDER BY confidence_score DESC, target_word
        LIMIT ?
        """
        
        search_pattern = f"%{source_word.lower()}%"
        cursor.execute(query, (search_pattern, search_pattern, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []

def format_rhyme_results(source_word, results):
    """Format and display rhyme search results"""
    
    if not results:
        print(f"❌ No rhymes found for '{source_word}'")
        return
    
    print(f"🎯 TARGET RHYMES for '{source_word.upper()}':")
    print("=" * 60)
    
    # Group by target word to show variety
    target_groups = {}
    for result in results:
        target_word = result[0]
        if target_word not in target_groups:
            target_groups[target_word] = []
        target_groups[target_word].append(result)
    
    count = 0
    for target_word, matches in target_groups.items():
        if count >= 15:  # Limit display
            break
            
        # Show best match for each target word
        best_match = matches[0]  # Already sorted by confidence
        
        target, artist, song, pattern, distance, confidence, source_ctx, target_ctx, cultural = best_match
        
        count += 1
        print(f"{count:2d}. {target.upper()}")
        print(f"    📝 Pattern: {pattern}")
        print(f"    🎤 Source: {artist} - {song}")
        print(f"    📏 Distance: {distance} line{'s' if distance > 1 else ''} apart")
        print(f"    📊 Confidence: {confidence:.2f}")
        
        if len(matches) > 1:
            print(f"    🔄 Found in {len(matches)} different songs")
        
        print()

def demo_searches():
    """Run some demo searches to show the system working"""
    
    print("🎵 RhymeRarity Songs Database - Rhyme Search Demo")
    print("=" * 60)
    
    # Check if database exists
    db_path = "songs_patterns_unified.db"
    if not os.path.exists(db_path):
        db_path = "/home/claude/songs_patterns_unified.db"
        
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run load_songs_to_database.py first")
        return
    
    print(f"✅ Using database: {db_path}")
    
    # Demo searches with common rap words
    demo_words = ["love", "night", "time", "mind", "flow"]
    
    for word in demo_words:
        print(f"\n" + "=" * 80)
        results = search_target_rhymes(word, db_path, limit=30)
        format_rhyme_results(word, results)
        
        if word != demo_words[-1]:  # Not the last word
            input("Press Enter to continue to next search...")

def interactive_search():
    """Interactive rhyme search"""
    
    db_path = "songs_patterns_unified.db"
    if not os.path.exists(db_path):
        db_path = "/home/claude/songs_patterns_unified.db"
        
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run load_songs_to_database.py first")
        return
    
    print("🎵 RhymeRarity Interactive Rhyme Search")
    print("=" * 50)
    print("Enter words to find target rhymes, or 'quit' to exit")
    
    while True:
        try:
            word = input("\n🔍 Enter word to find rhymes for: ").strip().lower()
            
            if word in ['quit', 'exit', 'q']:
                print("👋 Thanks for using RhymeRarity!")
                break
                
            if not word:
                continue
                
            results = search_target_rhymes(word, db_path, limit=25)
            format_rhyme_results(word, results)
            
        except KeyboardInterrupt:
            print("\n👋 Thanks for using RhymeRarity!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Run demo searches")
    print("2. Interactive search")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        demo_searches()
    elif choice == "2":
        interactive_search()
    else:
        print("Running demo searches...")
        demo_searches()
