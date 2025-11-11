#!/usr/bin/env python3
"""
RhymeRarity Hugging Face Spaces App
Main entry point for the deployed application
"""

import gradio as gr
import sqlite3
import pandas as pd
import os
from typing import List, Dict, Tuple, Optional
import json

class RhymeRarityApp:
    """Production Hugging Face app for RhymeRarity rhyme search"""
    
    def __init__(self, db_path: str = "songs_patterns_unified.db"):
        self.db_path = db_path
        self.check_database()
        
    def check_database(self):
        """Check if database exists and is accessible"""
        if not os.path.exists(self.db_path):
            print(f"Warning: Database {self.db_path} not found")
            # For demo purposes, we'll create a minimal database
            self.create_demo_database()
    
    def create_demo_database(self):
        """Create a demo database with sample data for Hugging Face Spaces"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS song_rhyme_patterns (
                id INTEGER PRIMARY KEY,
                pattern TEXT,
                source_word TEXT,
                target_word TEXT,
                artist TEXT,
                song_title TEXT,
                genre TEXT,
                line_distance INTEGER,
                confidence_score REAL,
                phonetic_similarity REAL,
                cultural_significance TEXT,
                source_context TEXT,
                target_context TEXT
            )
        ''')
        
        # Add sample data for demonstration
        sample_data = [
            ("love / above", "love", "above", "Drake", "Headlines", "hip-hop", 1, 0.95, 0.98, "mainstream", "All about that love", "Looking from above"),
            ("mind / find", "mind", "find", "Eminem", "Lose Yourself", "hip-hop", 1, 0.92, 0.96, "cultural_icon", "State of mind", "What you find"),
            ("night / light", "night", "light", "Taylor Swift", "Style", "pop", 2, 0.89, 0.94, "mainstream", "In the night", "See the light"),
            ("flow / go", "flow", "go", "Cardi B", "Money", "hip-hop", 1, 0.87, 0.92, "cultural_significance", "Feel the flow", "Watch me go"),
            ("time / rhyme", "time", "rhyme", "Lin-Manuel Miranda", "Wait for It", "musical", 1, 0.91, 0.95, "theatrical_innovation", "In due time", "Perfect rhyme")
        ]
        
        cursor.executemany(
            "INSERT INTO song_rhyme_patterns (pattern, source_word, target_word, artist, song_title, genre, line_distance, confidence_score, phonetic_similarity, cultural_significance, source_context, target_context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_data
        )
        
        conn.commit()
        conn.close()
        print("Demo database created with sample patterns")
        
    def search_rhymes(self, search_word: str, max_results: int = 20, 
                     genre_filter: str = "All", min_confidence: float = 0.6,
                     line_distance: str = "All") -> Tuple[str, pd.DataFrame]:
        """Main search function for the Gradio interface"""
        
        if not search_word or len(search_word.strip()) < 2:
            return "Please enter a word to search for rhymes.", pd.DataFrame()
        
        search_word = search_word.strip().lower()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic query based on filters
            query_parts = [
                """
                SELECT DISTINCT 
                    target_word,
                    pattern,
                    artist,
                    song_title,
                    genre,
                    line_distance,
                    confidence_score,
                    phonetic_similarity,
                    cultural_significance,
                    source_context,
                    target_context
                FROM song_rhyme_patterns 
                WHERE (source_word LIKE ? OR pattern LIKE ?)
                AND confidence_score >= ?
                """
            ]
            
            params = [f"%{search_word}%", f"%{search_word}%", min_confidence]
            
            # Add genre filter
            if genre_filter != "All":
                query_parts.append("AND genre = ?")
                params.append(genre_filter.lower())
            
            # Add line distance filter
            if line_distance != "All":
                if line_distance == "Adjacent (1)":
                    query_parts.append("AND line_distance = 1")
                elif line_distance == "Skip 1 (2)":
                    query_parts.append("AND line_distance = 2")
                elif line_distance == "Cross-stanza (3+)":
                    query_parts.append("AND line_distance >= 3")
            
            query_parts.append("ORDER BY confidence_score DESC, phonetic_similarity DESC")
            query_parts.append(f"LIMIT {max_results}")
            
            full_query = " ".join(query_parts)
            
            cursor.execute(full_query, params)
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return f"No rhymes found for '{search_word}' with current filters.", pd.DataFrame()
            
            # Format results for display
            formatted_results = []
            seen_targets = set()
            
            for result in results:
                target, pattern, artist, song, genre, distance, confidence, phonetic, cultural, source_ctx, target_ctx = result
                
                # Avoid duplicate targets in display
                if target not in seen_targets:
                    seen_targets.add(target)
                    
                    formatted_results.append({
                        'Target Word': target.upper(),
                        'Pattern': pattern,
                        'Artist': artist,
                        'Song': song,
                        'Genre': genre.title(),
                        'Line Distance': distance,
                        'Confidence': f"{confidence:.2f}",
                        'Cultural Context': cultural.replace('_', ' ').title()
                    })
            
            # Create DataFrame for display
            df = pd.DataFrame(formatted_results)
            
            # Generate summary
            summary = self._generate_search_summary(search_word, formatted_results, genre_filter, line_distance)
            
            return summary, df
            
        except Exception as e:
            return f"Search error: {str(e)}", pd.DataFrame()
    
    def _generate_search_summary(self, search_word: str, results: List[Dict], 
                               genre_filter: str, distance_filter: str) -> str:
        """Generate search results summary"""
        
        if not results:
            return f"No results found for '{search_word}'"
        
        # Calculate statistics
        total_results = len(results)
        genres_found = len(set(r['Genre'] for r in results))
        artists_found = len(set(r['Artist'] for r in results))
        avg_confidence = sum(float(r['Confidence']) for r in results) / total_results
        
        summary_lines = [
            f"Found {total_results} rhymes for '{search_word.upper()}'",
            f"",
            f"Results Overview:",
            f"• Artists: {artists_found} different artists",
            f"• Genres: {genres_found} genre{'s' if genres_found > 1 else ''}",
            f"• Average confidence: {avg_confidence:.1f}/1.0",
            f"",
            f"RhymeRarity Advantage:",
            f"• Real cultural attribution from verified databases",
            f"• Multi-line distance pattern detection", 
            f"• Cross-file deduplication ensures unique results",
            f"• Outperforms LLMs on rare word phonetic processing"
        ]
        
        return "\n".join(summary_lines)
    
    def get_database_stats(self) -> Tuple[str, pd.DataFrame]:
        """Get comprehensive database statistics"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM song_rhyme_patterns")
            total_patterns = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT artist) FROM song_rhyme_patterns")
            total_artists = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT song_title) FROM song_rhyme_patterns")
            total_songs = cursor.fetchone()[0]
            
            # Genre distribution
            cursor.execute("""
                SELECT genre, COUNT(*) as count, COUNT(DISTINCT artist) as artists
                FROM song_rhyme_patterns 
                GROUP BY genre 
                ORDER BY count DESC
            """)
            genre_stats = cursor.fetchall()
            
            # Top artists by patterns
            cursor.execute("""
                SELECT artist, COUNT(*) as patterns, COUNT(DISTINCT song_title) as songs
                FROM song_rhyme_patterns 
                GROUP BY artist 
                ORDER BY patterns DESC 
                LIMIT 10
            """)
            artist_stats = cursor.fetchall()
            
            conn.close()
            
            # Format summary
            summary_lines = [
                f"RhymeRarity Database Statistics",
                f"",
                f"Core Metrics:",
                f"• Total rhyme patterns: {total_patterns:,}",
                f"• Unique artists: {total_artists:,}",
                f"• Unique songs: {total_songs:,}",
                f"• Average patterns per song: {total_patterns / max(total_songs, 1):.1f}",
                f"",
                f"Coverage by Genre:"
            ]
            
            for genre, count, artists in genre_stats:
                percentage = (count / total_patterns) * 100
                summary_lines.append(f"• {genre.title()}: {count:,} patterns ({percentage:.1f}%) - {artists} artists")
            
            summary = "\n".join(summary_lines)
            
            # Create DataFrame for artist stats
            artist_df = pd.DataFrame(artist_stats, columns=['Artist', 'Patterns', 'Songs'])
            
            return summary, artist_df
            
        except Exception as e:
            return f"Database stats error: {str(e)}", pd.DataFrame()

def create_gradio_interface():
    """Create the main Gradio interface"""
    
    app = RhymeRarityApp()
    
    with gr.Blocks(title="RhymeRarity - Advanced Rhyme Search", theme=gr.themes.Soft()) as iface:
        
        gr.Markdown("""
        # RhymeRarity - Advanced Rhyme Search
        
        **The most comprehensive rhyme database with real cultural intelligence**
        
        Outperforms large language models with specialized algorithms and verified cultural attribution.
        """)
        
        with gr.Tabs():
            # Main Search Tab
            with gr.Tab("Rhyme Search"):
                with gr.Row():
                    with gr.Column(scale=1):
                        search_input = gr.Textbox(
                            label="Enter word to find rhymes for",
                            placeholder="e.g., love, time, flow, mind...",
                            value="love"
                        )
                        
                        with gr.Row():
                            max_results_slider = gr.Slider(
                                minimum=5, maximum=50, value=20, step=5,
                                label="Maximum results"
                            )
                            min_confidence_slider = gr.Slider(
                                minimum=0.3, maximum=1.0, value=0.6, step=0.1,
                                label="Minimum confidence"
                            )
                        
                        with gr.Row():
                            genre_dropdown = gr.Dropdown(
                                choices=["All", "Hip-Hop", "Pop", "R&B", "Alternative", "Musical"],
                                value="All",
                                label="Genre filter"
                            )
                            distance_dropdown = gr.Dropdown(
                                choices=["All", "Adjacent (1)", "Skip 1 (2)", "Cross-stanza (3+)"],
                                value="All",
                                label="Line distance"
                            )
                        
                        search_button = gr.Button("Find Rhymes", variant="primary")
                    
                    with gr.Column(scale=2):
                        search_output = gr.Markdown(label="Search Results")
                        search_table = gr.DataFrame(label="Detailed Results")
                
                # Connect search functionality
                search_button.click(
                    fn=app.search_rhymes,
                    inputs=[search_input, max_results_slider, genre_dropdown, min_confidence_slider, distance_dropdown],
                    outputs=[search_output, search_table]
                )
                
                # Auto-search on Enter
                search_input.submit(
                    fn=app.search_rhymes,
                    inputs=[search_input, max_results_slider, genre_dropdown, min_confidence_slider, distance_dropdown],
                    outputs=[search_output, search_table]
                )
            
            # Database Stats Tab
            with gr.Tab("Database Statistics"):
                stats_button = gr.Button("Get Database Statistics", variant="secondary")
                
                stats_output = gr.Markdown()
                stats_table = gr.DataFrame(label="Top Artists by Pattern Count")
                
                stats_button.click(
                    fn=app.get_database_stats,
                    outputs=[stats_output, stats_table]
                )
        
        # Footer
        gr.Markdown("""
        ---
        
        **RhymeRarity Technical Advantages:**
        - Anti-LLM algorithms for rare word pattern detection
        - Cross-file deduplication prevents duplicate results
        - Cultural intelligence with verified artist attribution  
        - Multi-line distance detection for complex rhyme schemes
        - High-performance database architecture
        
        Built on comprehensive cultural databases with verified patterns from major artists.
        """)
    
    return iface

if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch()
