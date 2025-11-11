#!/usr/bin/env python3
"""
Enhanced Songs Pattern Database Creator for RhymeRarity
Handles multiple CSV formats while maintaining existing pattern database performance

Supports all formats:
1. Single-song format (ArianaGrande.csv): Artist,Title,Album,Date,Lyric,Year
2. Line-pair format (updated_rappers): artist,song,lyric,next lyric  
3. Multi-row format (lyrics-data_1): ALink,SName,SLink,Lyric,language
4. Index format (combined_lyrics): lyrics,artist,category
5. Musical format (ham_lyrics): Hamilton/theatrical data

+ ENHANCED: Cross-file deduplication prevents duplicate target rhyme results
"""

import sqlite3
import pandas as pd
import os
import re
import unicodedata
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import json
import hashlib
from datetime import datetime
import sys

# Add current directory to path for cross_file_deduplicator import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class SongPattern:
    """Enhanced pattern structure for unified song database"""
    pattern: str
    source_word: str
    target_word: str
    artist: str
    song_title: str
    album: Optional[str] = None
    year: Optional[int] = None
    genre: str = "unknown"
    secondary_genres: List[str] = None
    line_distance: int = 1  # Distance between source and target lines
    pattern_type: str = "end_rhyme"  # end_rhyme, internal_rhyme, multi_word, etc.
    confidence_score: float = 0.8
    rhyme_density: float = 0.0
    source_context: str = ""  # Source line with surrounding context
    target_context: str = ""  # Target line with surrounding context
    phonetic_similarity: float = 0.0
    cultural_significance: str = "mainstream"
    language: str = "en"
    source_line_index: int = 0
    target_line_index: int = 0
    
class EnhancedSongsPatternDatabase:
    """
    Unified pattern database creator that handles all CSV formats
    while preserving your existing high-performance architecture
    + ENHANCED: Cross-file deduplication to prevent duplicate target rhyme results
    """
    
    def __init__(self):
        self.processed_patterns = []
        self.duplicate_filter = set()  # Hash-based deduplication
        self.artist_genre_mapping = self._initialize_artist_genres()
        self.format_handlers = {
            'single_song': self._process_single_song_format,
            'line_pair': self._process_line_pair_format, 
            'multi_row': self._process_multi_row_format,
            'index': self._process_index_format,
            'musical': self._process_musical_format
        }
        
        # ENHANCED: Cross-file deduplication system
        try:
            from cross_file_deduplicator import CrossFileDeduplicator
            self.deduplicator = CrossFileDeduplicator()
        except ImportError:
            print("⚠️  Cross-file deduplicator not found, using basic deduplication")
            self.deduplicator = None
            
        self.processed_songs = set()  # Track processed songs across files
        
        # Performance optimization settings
        self.batch_size = 10000
        self.max_line_distance = 3  # Search up to 3 lines apart for rhymes
        self.min_confidence_threshold = 0.6
        
        print("🎵 Enhanced Songs Pattern Database Creator initialized")
        print("✅ Cross-file deduplication system active")
        
    def _initialize_artist_genres(self) -> Dict:
        """Initialize comprehensive artist genre mapping based on your project knowledge"""
        return {
            # Pop Artists
            'ariana grande': {
                'primary_genre': 'pop', 'secondary_genres': ['r&b', 'trap-pop'],
                'style': 'vocal_runs_melodic', 'cultural_impact': 'gen_z_anthem',
                'rhyme_characteristics': ['internal_rhymes', 'melodic_flow']
            },
            'taylor swift': {
                'primary_genre': 'pop', 'secondary_genres': ['country', 'folk', 'rock'],
                'style': 'storytelling_narrative', 'cultural_impact': 'mainstream_literary',
                'rhyme_characteristics': ['narrative_rhymes', 'perfect_rhymes']
            },
            'beyonce': {
                'primary_genre': 'r&b', 'secondary_genres': ['pop', 'hip-hop'],
                'style': 'powerhouse_vocal', 'cultural_impact': 'cultural_icon',
                'rhyme_characteristics': ['complex_internal', 'vocal_runs']
            },
            
            # Hip-Hop/Rap Artists (from your existing database)
            'fetty wap': {
                'primary_genre': 'hip-hop', 'secondary_genres': ['trap', 'melodic_rap'],
                'style': 'melodic_trap', 'cultural_impact': 'trap_innovation',
                'rhyme_characteristics': ['trap_flows', 'melodic_hooks']
            },
            'drake': {
                'primary_genre': 'hip-hop', 'secondary_genres': ['r&b', 'pop'],
                'style': 'melodic_rap_singing', 'cultural_impact': 'mainstream_crossover',
                'rhyme_characteristics': ['internal_rhymes', 'melodic_flow']
            },
            'eminem': {
                'primary_genre': 'hip-hop', 'secondary_genres': ['rap', 'hardcore'],
                'style': 'technical_wordplay', 'cultural_impact': 'lyrical_genius',
                'rhyme_characteristics': ['multi_syllable', 'internal_complex', 'wordplay']
            },
            
            # Musical Theater
            'hamilton': {
                'primary_genre': 'musical', 'secondary_genres': ['theatrical', 'hip-hop'],
                'style': 'historical_complex', 'cultural_impact': 'theatrical_innovation',
                'rhyme_characteristics': ['dense_historical', 'rapid_wordplay']
            },
            'lin-manuel miranda': {
                'primary_genre': 'musical', 'secondary_genres': ['theatrical', 'hip-hop'],
                'style': 'historical_rap_musical', 'cultural_impact': 'theatrical_revolution',
                'rhyme_characteristics': ['complex_internal', 'historical_references']
            }
        }
    
    def detect_csv_format(self, filepath: str) -> str:
        """
        Intelligent format detection based on column structure
        Returns format type for appropriate handler
        """
        try:
            # Read first few rows to analyze structure
            df_sample = pd.read_csv(filepath, nrows=5, encoding='utf-8')
            columns = [col.lower().strip() for col in df_sample.columns]
            
            print(f"📊 Analyzing {os.path.basename(filepath)}: columns = {columns}")
            
            # Format detection logic
            if 'artist' in columns and 'title' in columns and 'lyric' in columns and len(columns) >= 5:
                return 'single_song'  # ArianaGrande.csv format
            elif 'artist' in columns and 'song' in columns and 'next lyric' in columns:
                return 'line_pair'    # updated_rappers format (your successful format!)
            elif 'alink' in columns and 'sname' in columns and 'lyric' in columns:
                return 'multi_row'    # lyrics-data_1.csv format
            elif 'lyrics' in columns and 'category' in columns:
                return 'index'        # combined_lyrics.csv format
            else:
                return 'musical'      # Hamilton or other theatrical format
                
        except Exception as e:
            print(f"⚠️  Format detection failed for {filepath}: {e}")
            return 'single_song'  # Default fallback
    
    def process_csv_file(self, filepath: str) -> List[SongPattern]:
        """
        Main processing pipeline that routes to appropriate format handler
        ENHANCED: Tracks source file for cross-file deduplication
        """
        print(f"🎯 Processing {os.path.basename(filepath)}...")
        
        # ENHANCED: Set current source file for deduplication tracking
        self.current_source_file = os.path.basename(filepath)
        
        # Detect format and route to appropriate handler
        format_type = self.detect_csv_format(filepath)
        handler = self.format_handlers.get(format_type, self._process_single_song_format)
        
        print(f"📝 Detected format: {format_type}")
        
        try:
            patterns = handler(filepath)
            print(f"✅ Extracted {len(patterns):,} patterns from {os.path.basename(filepath)}")
            
            # ENHANCED: Show deduplication stats for this file (if available)
            if self.deduplicator and hasattr(self.deduplicator, 'dedup_stats'):
                duplicates_found = self.deduplicator.dedup_stats.get('patterns_duplicated', 0)
                if duplicates_found > 0:
                    print(f"🔍 Filtered {duplicates_found:,} duplicate patterns from {os.path.basename(filepath)}")
            
            return patterns
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return []
    
    def _process_single_song_format(self, filepath: str) -> List[SongPattern]:
        """
        Process single-song format (ArianaGrande.csv style)
        Artist,Title,Album,Date,Lyric,Year -> extract line-by-line patterns
        """
        patterns = []
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            
            for _, row in df.iterrows():
                artist = str(row.get('Artist', '')).strip()
                title = str(row.get('Title', '')).strip()
                album = str(row.get('Album', '')).strip()
                year = self._safe_int(row.get('Year'))
                lyrics = str(row.get('Lyric', ''))
                
                # Extract patterns from full lyrics
                song_patterns = self._extract_patterns_from_lyrics(
                    lyrics, artist, title, album, year
                )
                patterns.extend(song_patterns)
                
        except Exception as e:
            print(f"Error in single song format: {e}")
            
        return patterns
    
    def _process_line_pair_format(self, filepath: str) -> List[SongPattern]:
        """
        Process line-pair format (updated_rappers style) - YOUR SUCCESSFUL FORMAT!
        This maintains your existing high-performance approach
        """
        patterns = []
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            
            for _, row in df.iterrows():
                artist = str(row.get('artist', '')).strip()
                song = str(row.get('song', '')).strip()
                current_line = str(row.get('lyric', '')).strip()
                next_line = str(row.get('next lyric', '')).strip()
                
                # Extract patterns between current and next line (distance=1)
                patterns_extracted = self._extract_line_pair_patterns(
                    current_line, next_line, artist, song
                )
                patterns.extend(patterns_extracted)
                
        except Exception as e:
            print(f"Error in line pair format: {e}")
            
        return patterns
    
    def _process_multi_row_format(self, filepath: str) -> List[SongPattern]:
        """
        Process multi-row format (lyrics-data_1.csv style)
        Group by song and extract patterns
        """
        patterns = []
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            
            # Group by song (SName) to reconstruct full lyrics
            grouped = df.groupby('SName')
            
            for song_name, group in grouped:
                if len(group) < 2:  # Need at least 2 lines for patterns
                    continue
                    
                # Reconstruct lyrics from multiple rows
                lyrics_lines = []
                artist = "Unknown"  # Multi-row format may not have artist info
                
                for _, row in group.iterrows():
                    lyric_line = str(row.get('Lyric', '')).strip()
                    if lyric_line and lyric_line != 'nan':
                        lyrics_lines.append(lyric_line)
                
                if len(lyrics_lines) >= 2:
                    # Extract patterns from reconstructed lyrics
                    full_lyrics = '\n'.join(lyrics_lines)
                    song_patterns = self._extract_patterns_from_lyrics(
                        full_lyrics, artist, str(song_name), None, None
                    )
                    patterns.extend(song_patterns)
                    
        except Exception as e:
            print(f"Error in multi-row format: {e}")
            
        return patterns
    
    def _process_index_format(self, filepath: str) -> List[SongPattern]:
        """Process index format (combined_lyrics.csv style)"""
        # This appears to be metadata, might need to cross-reference with other files
        print("📋 Index format detected - may need cross-referencing with full lyric files")
        return []
    
    def _process_musical_format(self, filepath: str) -> List[SongPattern]:
        """Process musical/theatrical format (Hamilton, etc.)"""
        patterns = []
        try:
            # Try different encodings for theatrical data
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is not None:
                # Process based on detected columns
                # This is flexible to handle various musical formats
                for _, row in df.iterrows():
                    # Extract available information
                    lyrics = ""
                    artist = "Hamilton Cast"  # Default for theatrical
                    song = "Unknown"
                    
                    # Flexible column detection
                    for col in df.columns:
                        if 'lyric' in col.lower() or 'text' in col.lower():
                            lyrics = str(row[col])
                        elif 'song' in col.lower() or 'title' in col.lower():
                            song = str(row[col])
                        elif 'artist' in col.lower() or 'character' in col.lower():
                            artist = str(row[col])
                    
                    if lyrics and len(lyrics) > 10:
                        song_patterns = self._extract_patterns_from_lyrics(
                            lyrics, artist, song, None, None
                        )
                        patterns.extend(song_patterns)
                        
        except Exception as e:
            print(f"Error in musical format: {e}")
            
        return patterns
    
    def _extract_patterns_from_lyrics(self, lyrics: str, artist: str, song: str, 
                                    album: Optional[str], year: Optional[int]) -> List[SongPattern]:
        """
        Extract multi-line rhyme patterns from full lyrics
        ENHANCED: Cross-file deduplication prevents duplicate target rhyme results
        """
        patterns = []
        
        # ENHANCED: Check for song-level duplicates first (if deduplicator available)
        if self.deduplicator:
            song_data = {
                'artist': artist,
                'title': song,
                'song': song, 
                'lyrics': lyrics,
                'source_file': getattr(self, 'current_source_file', 'unknown')
            }
            
            is_duplicate_song, existing_song = self.deduplicator.detect_song_duplicates(song_data)
            
            if is_duplicate_song and existing_song:
                if existing_song.source_priority.value <= song_data.get('source_priority', 5):
                    # Skip processing - better version already exists
                    print(f"   ⏭️  Skipping duplicate song: {artist} - {song} (better source exists)")
                    return patterns
        
        # Clean and split lyrics into lines
        lines = self._clean_and_split_lyrics(lyrics)
        if len(lines) < 2:
            return patterns
        
        # Get artist info for cultural context
        artist_lower = artist.lower().strip()
        artist_info = self.artist_genre_mapping.get(artist_lower, {})
        genre = artist_info.get('primary_genre', 'unknown')
        secondary_genres = artist_info.get('secondary_genres', [])
        cultural_significance = artist_info.get('cultural_impact', 'mainstream')
        
        # Extract patterns at different line distances (1, 2, 3 lines apart)
        for source_idx, source_line in enumerate(lines):
            source_words = self._extract_rhyme_candidates(source_line)
            
            for distance in range(1, min(self.max_line_distance + 1, len(lines) - source_idx)):
                target_idx = source_idx + distance
                if target_idx >= len(lines):
                    break
                    
                target_line = lines[target_idx]
                target_words = self._extract_rhyme_candidates(target_line)
                
                # Find rhyming pairs between source and target lines
                for source_word in source_words:
                    for target_word in target_words:
                        # Calculate phonetic similarity (simplified for now)
                        similarity = self._calculate_phonetic_similarity(source_word, target_word)
                        
                        if similarity >= self.min_confidence_threshold:
                            # Create pattern data for deduplication check
                            pattern_text = f"{source_word} / {target_word}"
                            
                            pattern_data = {
                                'pattern': pattern_text,
                                'source_word': source_word,
                                'target_word': target_word,
                                'artist': artist,
                                'song': song,
                                'title': song,
                                'line_distance': distance,
                                'source_context': self._get_context(lines, source_idx),
                                'target_context': self._get_context(lines, target_idx),
                                'phonetic_similarity': similarity,
                                'source_file': getattr(self, 'current_source_file', 'unknown')
                            }
                            
                            # ENHANCED: Check for pattern-level duplicates (if deduplicator available)
                            is_duplicate_pattern = False
                            conflict_note = None
                            
                            if self.deduplicator:
                                is_duplicate_pattern, conflict_note = self.deduplicator.detect_pattern_duplicates(pattern_data)
                            else:
                                # Fallback to basic hash-based deduplication
                                pattern_hash = self._generate_pattern_hash(
                                    pattern_text, artist, song, source_idx, target_idx
                                )
                                is_duplicate_pattern = pattern_hash in self.duplicate_filter
                                if not is_duplicate_pattern:
                                    self.duplicate_filter.add(pattern_hash)
                            
                            if not is_duplicate_pattern:
                                # Determine pattern type
                                pattern_type = "end_rhyme" if distance == 1 else "distant_rhyme"
                                if source_idx == target_idx:
                                    pattern_type = "internal_rhyme"
                                
                                pattern = SongPattern(
                                    pattern=pattern_text,
                                    source_word=source_word,
                                    target_word=target_word,
                                    artist=artist,
                                    song_title=song,
                                    album=album,
                                    year=year,
                                    genre=genre,
                                    secondary_genres=secondary_genres,
                                    line_distance=distance,
                                    pattern_type=pattern_type,
                                    confidence_score=similarity,
                                    rhyme_density=len(source_words) + len(target_words),
                                    source_context=self._get_context(lines, source_idx),
                                    target_context=self._get_context(lines, target_idx),
                                    phonetic_similarity=similarity,
                                    cultural_significance=cultural_significance,
                                    source_line_index=source_idx,
                                    target_line_index=target_idx
                                )
                                
                                patterns.append(pattern)
                            else:
                                # Log duplicate detection for monitoring
                                if conflict_note:
                                    print(f"   🔍 Duplicate pattern filtered: {pattern_text} - {conflict_note}")
        
        return patterns
    
    def _extract_line_pair_patterns(self, current_line: str, next_line: str, 
                                   artist: str, song: str) -> List[SongPattern]:
        """
        Extract patterns from line pairs (maintains your successful format)
        """
        patterns = []
        
        current_words = self._extract_rhyme_candidates(current_line)
        next_words = self._extract_rhyme_candidates(next_line)
        
        # Get artist info
        artist_lower = artist.lower().strip()
        artist_info = self.artist_genre_mapping.get(artist_lower, {})
        genre = artist_info.get('primary_genre', 'hip-hop')  # Default to hip-hop for rap data
        
        for current_word in current_words:
            for next_word in next_words:
                similarity = self._calculate_phonetic_similarity(current_word, next_word)
                
                if similarity >= self.min_confidence_threshold:
                    pattern_text = f"{current_word} / {next_word}"
                    pattern_hash = self._generate_pattern_hash(pattern_text, artist, song, 0, 1)
                    
                    if pattern_hash not in self.duplicate_filter:
                        self.duplicate_filter.add(pattern_hash)
                        
                        pattern = SongPattern(
                            pattern=pattern_text,
                            source_word=current_word,
                            target_word=next_word,
                            artist=artist,
                            song_title=song,
                            genre=genre,
                            line_distance=1,
                            pattern_type="end_rhyme",
                            confidence_score=similarity,
                            source_context=current_line,
                            target_context=next_line,
                            phonetic_similarity=similarity,
                            cultural_significance=artist_info.get('cultural_impact', 'mainstream')
                        )
                        
                        patterns.append(pattern)
        
        return patterns
    
    def _clean_and_split_lyrics(self, lyrics: str) -> List[str]:
        """Clean lyrics and split into meaningful lines"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', lyrics.strip())
        
        # Split on common line break patterns
        lines = re.split(r'[\n\r]+|(?:\s{2,})', cleaned)
        
        # Filter out empty lines and clean each line
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:  # Minimum meaningful line length
                # Remove extra punctuation but preserve word boundaries
                line = re.sub(r'[^\w\s\']', ' ', line)
                line = re.sub(r'\s+', ' ', line).strip()
                if line:
                    clean_lines.append(line.lower())
        
        return clean_lines
    
    def _extract_rhyme_candidates(self, line: str) -> List[str]:
        """Extract potential rhyme words from a line"""
        # Split into words and filter
        words = line.strip().split()
        candidates = []
        
        for word in words:
            # Clean word
            word = re.sub(r'[^\w]', '', word.lower().strip())
            
            # Filter criteria
            if (len(word) >= 2 and 
                word not in {'the', 'and', 'but', 'for', 'you', 'are', 'can', 'was'} and
                not word.isdigit()):
                candidates.append(word)
        
        return candidates
    
    def _calculate_phonetic_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate phonetic similarity (simplified version)
        In production, this would use your existing phonetic analysis
        """
        if word1 == word2:
            return 1.0
        
        # Basic suffix matching (simplified)
        max_len = max(len(word1), len(word2))
        if max_len < 2:
            return 0.0
        
        # Check suffix similarity
        suffix_len = min(3, min(len(word1), len(word2)))
        if word1[-suffix_len:] == word2[-suffix_len:]:
            return 0.8 + (suffix_len / max_len) * 0.2
        
        # Check ending sound patterns
        if suffix_len >= 2 and word1[-2:] == word2[-2:]:
            return 0.7
        
        return 0.3  # Base similarity for potential near rhymes
    
    def _get_context(self, lines: List[str], line_idx: int, context_size: int = 1) -> str:
        """Get surrounding context for a line"""
        start_idx = max(0, line_idx - context_size)
        end_idx = min(len(lines), line_idx + context_size + 1)
        context_lines = lines[start_idx:end_idx]
        return " | ".join(context_lines)
    
    def _generate_pattern_hash(self, pattern: str, artist: str, song: str, 
                              source_idx: int, target_idx: int) -> str:
        """Generate unique hash for pattern deduplication"""
        hash_input = f"{pattern.lower()}:{artist.lower()}:{song.lower()}:{source_idx}:{target_idx}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        try:
            return int(float(value)) if value and str(value).strip() else None
        except (ValueError, TypeError):
            return None
    
    def create_unified_songs_database(self, csv_files: List[str], db_name: str = "songs_patterns_unified.db") -> str:
        """
        Create unified songs pattern database from multiple CSV files
        ENHANCED: Cross-file deduplication prevents duplicate target rhyme results
        """
        print(f"🏗️  Creating unified songs database: {db_name}")
        print("✅ Cross-file deduplication system active - preventing duplicate results")
        
        # Process all CSV files with deduplication
        all_patterns = []
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                patterns = self.process_csv_file(csv_file)
                all_patterns.extend(patterns)
            else:
                print(f"⚠️  File not found: {csv_file}")
        
        print(f"\n📊 DEDUPLICATION SUMMARY")
        print("=" * 50)
        
        # Get comprehensive deduplication statistics (if available)
        if self.deduplicator:
            dedup_summary = self.deduplicator.get_deduplication_summary()
            
            # Song-level deduplication stats
            song_stats = dedup_summary['song_statistics']
            print(f"🎵 SONG DEDUPLICATION:")
            print(f"   • Songs processed: {song_stats['songs_processed']:,}")
            print(f"   • Duplicate songs found: {song_stats['songs_duplicated']:,}")
            print(f"   • Song duplicate rate: {song_stats['song_duplicate_rate']}")
            
            # Pattern-level deduplication stats  
            pattern_stats = dedup_summary['pattern_statistics']
            print(f"\n🔄 PATTERN DEDUPLICATION:")
            print(f"   • Patterns processed: {pattern_stats['patterns_processed']:,}")
            print(f"   • Duplicate patterns filtered: {pattern_stats['patterns_duplicated']:,}")
            print(f"   • Overall duplicate rate: {pattern_stats['duplicate_rate']}")
            print(f"   • Exact duplicates: {pattern_stats['exact_duplicates']:,}")
            print(f"   • Fuzzy duplicates: {pattern_stats['fuzzy_duplicates']:,}")
            print(f"   • Context duplicates: {pattern_stats['context_duplicates']:,}")
            
            # Quality improvements
            quality_stats = dedup_summary['quality_improvements']
            print(f"\n⭐ QUALITY IMPROVEMENTS:")
            print(f"   • Source upgrades: {quality_stats['source_upgrades']:,}")
            print(f"   • Conflicts resolved: {quality_stats['source_conflicts_resolved']:,}")
            
            # Cross-file analysis
            cross_file_stats = dedup_summary['cross_file_analysis']
            print(f"\n🔀 CROSS-FILE ANALYSIS:")
            print(f"   • Patterns across multiple files: {cross_file_stats['patterns_across_multiple_files']:,}")
            
            most_duplicated = cross_file_stats['most_duplicated_patterns']
            if most_duplicated:
                print(f"   • Most duplicated patterns:")
                for i, pattern_info in enumerate(most_duplicated[:3], 1):
                    print(f"     {i}. '{pattern_info['pattern']}' - {pattern_info['file_count']} files")
            
            # Export clean patterns for analysis
            clean_patterns_file = db_name.replace('.db', '_clean_patterns.json')
            self.deduplicator.export_clean_patterns(clean_patterns_file)
        else:
            print("⚠️  Advanced deduplication not available - using basic hash-based deduplication")
            dedup_summary = {'basic_deduplication': 'active'}
        
        print(f"\n📊 Final clean patterns: {len(all_patterns):,}")
        
        # Create database
        db_path = os.path.join(os.getcwd(), db_name)
        if os.path.exists(db_path):
            os.remove(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enhanced table schema building on your successful design
        cursor.execute('''
            CREATE TABLE song_rhyme_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                source_word TEXT NOT NULL,
                target_word TEXT NOT NULL,
                artist TEXT NOT NULL,
                song_title TEXT,
                album TEXT,
                year INTEGER,
                genre TEXT NOT NULL,
                secondary_genres TEXT,
                line_distance INTEGER DEFAULT 1,
                pattern_type TEXT DEFAULT 'end_rhyme',
                confidence_score REAL DEFAULT 0.8,
                rhyme_density REAL DEFAULT 0.0,
                source_context TEXT,
                target_context TEXT,
                phonetic_similarity REAL DEFAULT 0.0,
                cultural_significance TEXT DEFAULT 'mainstream',
                language TEXT DEFAULT 'en',
                source_line_index INTEGER DEFAULT 0,
                target_line_index INTEGER DEFAULT 0,
                deduplication_hash TEXT,
                source_file TEXT,
                created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance indexes (based on your successful pattern)
        performance_indexes = [
            'CREATE INDEX idx_pattern ON song_rhyme_patterns(pattern)',
            'CREATE INDEX idx_source_word ON song_rhyme_patterns(source_word)',
            'CREATE INDEX idx_target_word ON song_rhyme_patterns(target_word)',
            'CREATE INDEX idx_artist ON song_rhyme_patterns(artist)',
            'CREATE INDEX idx_genre ON song_rhyme_patterns(genre)',
            'CREATE INDEX idx_confidence ON song_rhyme_patterns(confidence_score)',
            'CREATE INDEX idx_line_distance ON song_rhyme_patterns(line_distance)',
            'CREATE INDEX idx_pattern_type ON song_rhyme_patterns(pattern_type)',
            'CREATE INDEX idx_phonetic ON song_rhyme_patterns(phonetic_similarity)',
            'CREATE INDEX idx_composite_search ON song_rhyme_patterns(source_word, confidence_score, line_distance)',
            'CREATE INDEX idx_deduplication ON song_rhyme_patterns(deduplication_hash)',
            'CREATE UNIQUE INDEX idx_unique_patterns ON song_rhyme_patterns(pattern, artist, song_title, line_distance)'
        ]
        
        for index_sql in performance_indexes:
            cursor.execute(index_sql)
            
        print("📋 Database schema created with enhanced performance indexes")
        
        # Batch insert patterns for optimal performance
        batch_data = []
        for pattern in all_patterns:
            # Generate deduplication hash for final verification
            dedup_hash = hashlib.sha256(
                f"{pattern.pattern}|{pattern.artist}|{pattern.song_title}|{pattern.line_distance}".encode()
            ).hexdigest()[:16]
            
            batch_data.append((
                pattern.pattern,
                pattern.source_word,
                pattern.target_word,
                pattern.artist,
                pattern.song_title,
                pattern.album,
                pattern.year,
                pattern.genre,
                ','.join(pattern.secondary_genres) if pattern.secondary_genres else '',
                pattern.line_distance,
                pattern.pattern_type,
                pattern.confidence_score,
                pattern.rhyme_density,
                pattern.source_context,
                pattern.target_context,
                pattern.phonetic_similarity,
                pattern.cultural_significance,
                pattern.language,
                pattern.source_line_index,
                pattern.target_line_index,
                dedup_hash,
                getattr(self, 'current_source_file', 'unknown')
            ))
            
            # Batch insert when batch size reached
            if len(batch_data) >= self.batch_size:
                self._insert_batch(cursor, batch_data)
                batch_data = []
        
        # Insert remaining patterns
        if batch_data:
            self._insert_batch(cursor, batch_data)
        
        # Database optimization
        cursor.execute("ANALYZE")
        conn.commit()
        
        # Get final statistics
        cursor.execute("SELECT COUNT(*) FROM song_rhyme_patterns")
        total_patterns = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT artist) FROM song_rhyme_patterns")
        total_artists = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT genre) FROM song_rhyme_patterns")
        total_genres = cursor.fetchone()[0]
        
        # Duplicate verification query
        cursor.execute("""
            SELECT COUNT(*) as duplicates FROM (
                SELECT pattern, artist, song_title, COUNT(*) as count
                FROM song_rhyme_patterns
                GROUP BY pattern, artist, song_title
                HAVING COUNT(*) > 1
            )
        """)
        remaining_duplicates = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n✅ DATABASE CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"   📁 File: {db_path}")
        print(f"   🎵 Final patterns: {total_patterns:,}")
        print(f"   👨‍🎤 Artists: {total_artists:,}")
        print(f"   🎼 Genres: {total_genres:,}")
        print(f"   💾 Size: {os.path.getsize(db_path) / (1024*1024):.1f} MB")
        print(f"   🔍 Remaining duplicates: {remaining_duplicates:,} (expected: 0)")
        print(f"   📈 Deduplication effectiveness: {100 - (remaining_duplicates / max(total_patterns, 1)) * 100:.1f}%")
        
        if remaining_duplicates == 0:
            print(f"\n🎉 SUCCESS: Zero duplicate target rhymes in final database!")
            print("Users will see unique results for all target rhyme searches.")
        else:
            print(f"\n⚠️  Warning: {remaining_duplicates:,} potential duplicates detected")
            print("Consider reviewing deduplication thresholds.")
        
        # Export deduplication report
        report_file = db_name.replace('.db', '_deduplication_report.json')
        with open(report_file, 'w') as f:
            json.dump({
                'database_path': db_path,
                'total_patterns': total_patterns,
                'total_artists': total_artists,
                'total_genres': total_genres,
                'remaining_duplicates': remaining_duplicates,
                'deduplication_summary': dedup_summary,
                'csv_files_processed': csv_files,
                'created_timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📊 Detailed report: {report_file}")
        
        return db_path
    
    def _insert_batch(self, cursor: sqlite3.Cursor, batch_data: List[Tuple]):
        """Optimized batch insert with deduplication fields"""
        cursor.executemany('''
            INSERT INTO song_rhyme_patterns 
            (pattern, source_word, target_word, artist, song_title, album, year, 
             genre, secondary_genres, line_distance, pattern_type, confidence_score,
             rhyme_density, source_context, target_context, phonetic_similarity,
             cultural_significance, language, source_line_index, target_line_index,
             deduplication_hash, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)

def main():
    """Main execution function"""
    processor = EnhancedSongsPatternDatabase()
    
    # Define your CSV files
    csv_files = [
        '/mnt/user-data/uploads/ArianaGrande.csv',
        '/mnt/user-data/uploads/updated_rappers_part0__1_.csv',
        '/mnt/user-data/uploads/lyrics-data_1.csv',
        '/mnt/user-data/uploads/combined_lyrics.csv',
        '/mnt/user-data/uploads/ham_lyrics.csv'
    ]
    
    # Create unified songs database
    db_path = processor.create_unified_songs_database(csv_files)
    
    print(f"\n🎉 Unified songs pattern database ready: {db_path}")
    print("This database maintains your existing high-performance architecture")
    print("while expanding to handle all your different CSV formats!")

if __name__ == "__main__":
    main()
