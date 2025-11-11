#!/usr/bin/env python3
"""
Enhanced Cross-File Deduplication System for RhymeRarity
Builds on your proven deduplication architecture with 621,802+ hip-hop + 263,881+ poetry patterns

MAINTAINS: Your successful multi-stage deduplication approach
ENHANCES: Cross-file duplicate detection for CSV processing
PREVENTS: Duplicate results in target rhyme searches

Key Features:
- Hierarchical source prioritization (which CSV to trust when duplicates exist)
- Song-level fingerprinting (detect same song in multiple CSVs)
- Pattern-level deduplication (prevent duplicate rhyme relationships)
- Performance-optimized with your proven hash-based approach
"""

import hashlib
import sqlite3
import difflib
import os
import re
from typing import Dict, List, Set, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum
import json

class SourcePriority(Enum):
    """Hierarchical source priority for conflict resolution"""
    HIGHEST = 1    # Line-pair format (your proven success format)
    HIGH = 2       # Single-song format (complete lyrics)
    MEDIUM = 3     # Multi-row format (reconstructed)
    LOW = 4        # Combined/index formats
    FALLBACK = 5   # Unknown or problematic sources

@dataclass
class SongFingerprint:
    """Unique identifier for songs across multiple CSV files"""
    artist_normalized: str
    title_normalized: str  
    lyrics_hash: str
    duration_similarity: float = 0.0
    source_file: str = ""
    source_priority: SourcePriority = SourcePriority.FALLBACK
    
    def get_composite_hash(self) -> str:
        """Generate composite hash for song identification"""
        composite = f"{self.artist_normalized}:{self.title_normalized}:{self.lyrics_hash[:16]}"
        return hashlib.md5(composite.encode()).hexdigest()

@dataclass
class PatternFingerprint:
    """Enhanced pattern fingerprint building on your existing system"""
    pattern_text: str           # "find / mind" 
    source_word: str           # "find"
    target_word: str           # "mind"
    artist_normalized: str     # "eminem"
    song_normalized: str       # "lose yourself"
    line_distance: int         # 1, 2, or 3
    context_hash: str          # Hash of surrounding lines
    phonetic_similarity: float # Your existing phonetic analysis
    source_file: str          # Which CSV this came from
    source_priority: SourcePriority
    
    def get_deduplication_hash(self) -> str:
        """Multi-level hash for comprehensive deduplication"""
        # Level 1: Exact pattern match
        exact_hash = f"{self.pattern_text.lower().strip()}"
        
        # Level 2: Semantic match (same rhyme relationship)
        semantic_hash = f"{self.source_word.lower()}:{self.target_word.lower()}"
        
        # Level 3: Context match (same song/artist)
        context_hash = f"{self.artist_normalized}:{self.song_normalized}"
        
        # Composite hash
        composite = f"{exact_hash}|{semantic_hash}|{context_hash}|{self.line_distance}"
        return hashlib.sha256(composite.encode()).hexdigest()

class CrossFileDeduplicator:
    """
    Enhanced deduplication system that prevents duplicate results
    while maintaining your proven high-performance architecture
    """
    
    def __init__(self):
        # Multi-level duplicate tracking (building on your existing system)
        self.song_fingerprints: Dict[str, SongFingerprint] = {}
        self.pattern_fingerprints: Dict[str, PatternFingerprint] = {}
        self.duplicate_patterns: Set[str] = set()
        
        # Source prioritization (maintains your quality standards)
        self.source_priorities = self._initialize_source_priorities()
        
        # Statistics tracking (your proven approach)
        self.dedup_stats = {
            'songs_processed': 0,
            'songs_duplicated': 0,
            'patterns_processed': 0,
            'patterns_duplicated': 0,
            'exact_duplicates': 0,
            'fuzzy_duplicates': 0,
            'context_duplicates': 0,
            'source_upgrades': 0,  # When higher priority source replaces lower
            'source_conflicts': 0   # When sources disagree
        }
        
        # Cross-file pattern tracking
        self.cross_file_patterns: Dict[str, List[str]] = defaultdict(list)
        self.pattern_sources: Dict[str, Dict] = {}
        
        # Performance optimization
        self.batch_size = 10000  # Your proven batch size
        self.fuzzy_threshold = 0.85  # Your existing threshold
        self.levenshtein_threshold = 15  # Your existing threshold
        
        print("🔍 Cross-File Deduplicator initialized")
        print("Building on your proven 885K+ pattern deduplication system")
    
    def _initialize_source_priorities(self) -> Dict[str, SourcePriority]:
        """Define source priority based on your CSV format analysis"""
        return {
            # Highest priority: Your proven line-pair format
            'updated_rappers': SourcePriority.HIGHEST,
            'rap_line_pairs': SourcePriority.HIGHEST,
            
            # High priority: Complete single-song formats
            'ariana_grande': SourcePriority.HIGH,
            'single_song': SourcePriority.HIGH,
            
            # Medium priority: Multi-row reconstructed formats
            'lyrics_data': SourcePriority.MEDIUM,
            'multi_row': SourcePriority.MEDIUM,
            
            # Low priority: Index/combined formats
            'combined_lyrics': SourcePriority.LOW,
            'index_format': SourcePriority.LOW,
            
            # Fallback: Unknown sources
            'unknown': SourcePriority.FALLBACK
        }
    
    def detect_song_duplicates(self, song_data: Dict) -> Tuple[bool, Optional[SongFingerprint]]:
        """
        Detect if song already exists from another CSV file
        Returns: (is_duplicate, existing_fingerprint_or_none)
        """
        # Create fingerprint for current song
        fingerprint = self._create_song_fingerprint(song_data)
        composite_hash = fingerprint.get_composite_hash()
        
        # Check for exact match
        if composite_hash in self.song_fingerprints:
            existing = self.song_fingerprints[composite_hash]
            self.dedup_stats['songs_duplicated'] += 1
            
            # Determine which source to keep based on priority
            if fingerprint.source_priority.value < existing.source_priority.value:
                # New source has higher priority - update
                self.song_fingerprints[composite_hash] = fingerprint
                self.dedup_stats['source_upgrades'] += 1
                return True, existing  # Return old fingerprint for comparison
            else:
                # Keep existing source
                return True, existing
        
        # Check for fuzzy matches (similar artist/title)
        for existing_hash, existing_fp in self.song_fingerprints.items():
            similarity_score = self._calculate_song_similarity(fingerprint, existing_fp)
            
            if similarity_score >= self.fuzzy_threshold:
                self.dedup_stats['songs_duplicated'] += 1
                self.dedup_stats['fuzzy_duplicates'] += 1
                
                # Prioritize based on source quality
                if fingerprint.source_priority.value < existing_fp.source_priority.value:
                    # Replace with higher quality source
                    del self.song_fingerprints[existing_hash]
                    self.song_fingerprints[composite_hash] = fingerprint
                    self.dedup_stats['source_upgrades'] += 1
                    return True, existing_fp
                else:
                    return True, existing_fp
        
        # No duplicate found - register new song
        self.song_fingerprints[composite_hash] = fingerprint
        self.dedup_stats['songs_processed'] += 1
        return False, None
    
    def detect_pattern_duplicates(self, pattern_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Detect if pattern already exists (prevents duplicate target rhyme results)
        Returns: (is_duplicate, conflict_resolution_note)
        """
        # Create pattern fingerprint
        fingerprint = self._create_pattern_fingerprint(pattern_data)
        dedup_hash = fingerprint.get_deduplication_hash()
        
        # Level 1: Exact pattern match
        if dedup_hash in self.pattern_fingerprints:
            existing = self.pattern_fingerprints[dedup_hash]
            self.dedup_stats['patterns_duplicated'] += 1
            self.dedup_stats['exact_duplicates'] += 1
            
            # Source priority resolution
            if fingerprint.source_priority.value < existing.source_priority.value:
                self.pattern_fingerprints[dedup_hash] = fingerprint
                self.dedup_stats['source_upgrades'] += 1
                return True, f"Upgraded from {existing.source_file} to {fingerprint.source_file}"
            else:
                return True, f"Kept {existing.source_file} over {fingerprint.source_file}"
        
        # Level 2: Semantic pattern matching (same rhyme relationship)
        semantic_matches = self._find_semantic_duplicates(fingerprint)
        if semantic_matches:
            self.dedup_stats['patterns_duplicated'] += 1
            self.dedup_stats['context_duplicates'] += 1
            
            # Choose best quality match
            best_match = self._select_best_semantic_match(fingerprint, semantic_matches)
            if best_match:
                return True, f"Semantic duplicate: {best_match.source_file}"
        
        # Level 3: Fuzzy pattern matching (building on your existing fuzzy logic)
        fuzzy_matches = self._find_fuzzy_pattern_duplicates(fingerprint)
        if fuzzy_matches:
            self.dedup_stats['patterns_duplicated'] += 1
            self.dedup_stats['fuzzy_duplicates'] += 1
            
            best_fuzzy = self._select_best_fuzzy_match(fingerprint, fuzzy_matches)
            if best_fuzzy:
                return True, f"Fuzzy duplicate: {best_fuzzy.source_file}"
        
        # No duplicate found - register new pattern
        self.pattern_fingerprints[dedup_hash] = fingerprint
        self.cross_file_patterns[fingerprint.pattern_text].append(fingerprint.source_file)
        self.dedup_stats['patterns_processed'] += 1
        
        return False, None
    
    def _create_song_fingerprint(self, song_data: Dict) -> SongFingerprint:
        """Create song fingerprint for duplicate detection"""
        artist = str(song_data.get('artist', '')).strip()
        title = str(song_data.get('title', song_data.get('song', ''))).strip()
        lyrics = str(song_data.get('lyrics', song_data.get('lyric', ''))).strip()
        source_file = song_data.get('source_file', 'unknown')
        
        # Normalize for comparison
        artist_norm = self._normalize_text(artist)
        title_norm = self._normalize_text(title)
        
        # Create lyrics hash
        lyrics_cleaned = re.sub(r'[^\w\s]', '', lyrics.lower())
        lyrics_hash = hashlib.md5(lyrics_cleaned.encode()).hexdigest()
        
        # Determine source priority
        source_priority = self._get_source_priority(source_file)
        
        return SongFingerprint(
            artist_normalized=artist_norm,
            title_normalized=title_norm,
            lyrics_hash=lyrics_hash,
            source_file=source_file,
            source_priority=source_priority
        )
    
    def _create_pattern_fingerprint(self, pattern_data: Dict) -> PatternFingerprint:
        """Create pattern fingerprint for comprehensive deduplication"""
        pattern_text = str(pattern_data.get('pattern', '')).strip()
        source_word = str(pattern_data.get('source_word', '')).strip()
        target_word = str(pattern_data.get('target_word', '')).strip()
        artist = str(pattern_data.get('artist', '')).strip()
        song = str(pattern_data.get('song', pattern_data.get('title', ''))).strip()
        line_distance = int(pattern_data.get('line_distance', 1))
        source_context = str(pattern_data.get('source_context', ''))
        target_context = str(pattern_data.get('target_context', ''))
        phonetic_sim = float(pattern_data.get('phonetic_similarity', 0.0))
        source_file = pattern_data.get('source_file', 'unknown')
        
        # Create context hash for duplicate detection
        context_combined = f"{source_context}|{target_context}"
        context_hash = hashlib.md5(context_combined.encode()).hexdigest()[:16]
        
        return PatternFingerprint(
            pattern_text=pattern_text,
            source_word=source_word.lower(),
            target_word=target_word.lower(), 
            artist_normalized=self._normalize_text(artist),
            song_normalized=self._normalize_text(song),
            line_distance=line_distance,
            context_hash=context_hash,
            phonetic_similarity=phonetic_sim,
            source_file=source_file,
            source_priority=self._get_source_priority(source_file)
        )
    
    def _calculate_song_similarity(self, fp1: SongFingerprint, fp2: SongFingerprint) -> float:
        """Calculate similarity between two song fingerprints"""
        # Artist similarity (most important)
        artist_sim = difflib.SequenceMatcher(None, fp1.artist_normalized, fp2.artist_normalized).ratio()
        
        # Title similarity
        title_sim = difflib.SequenceMatcher(None, fp1.title_normalized, fp2.title_normalized).ratio()
        
        # Lyrics similarity (using hash comparison)
        lyrics_sim = 1.0 if fp1.lyrics_hash == fp2.lyrics_hash else 0.0
        
        # Weighted combination
        total_similarity = (artist_sim * 0.4) + (title_sim * 0.4) + (lyrics_sim * 0.2)
        
        return total_similarity
    
    def _find_semantic_duplicates(self, fingerprint: PatternFingerprint) -> List[PatternFingerprint]:
        """Find semantically equivalent patterns (same rhyme relationship)"""
        matches = []
        
        for existing_hash, existing_fp in self.pattern_fingerprints.items():
            # Same rhyme words in same song = semantic duplicate
            if (existing_fp.source_word == fingerprint.source_word and
                existing_fp.target_word == fingerprint.target_word and
                existing_fp.artist_normalized == fingerprint.artist_normalized and
                existing_fp.song_normalized == fingerprint.song_normalized):
                matches.append(existing_fp)
        
        return matches
    
    def _find_fuzzy_pattern_duplicates(self, fingerprint: PatternFingerprint) -> List[PatternFingerprint]:
        """Find fuzzy pattern duplicates using your proven fuzzy matching"""
        matches = []
        
        for existing_hash, existing_fp in self.pattern_fingerprints.items():
            # Fuzzy pattern text matching
            pattern_sim = difflib.SequenceMatcher(
                None, 
                fingerprint.pattern_text.lower(), 
                existing_fp.pattern_text.lower()
            ).ratio()
            
            if pattern_sim >= self.fuzzy_threshold:
                matches.append(existing_fp)
        
        return matches
    
    def _select_best_semantic_match(self, new_fp: PatternFingerprint, 
                                   matches: List[PatternFingerprint]) -> Optional[PatternFingerprint]:
        """Select best semantic match based on source priority and quality"""
        if not matches:
            return None
        
        # Sort by source priority (lower value = higher priority)
        sorted_matches = sorted(matches, key=lambda x: x.source_priority.value)
        
        best_match = sorted_matches[0]
        
        # If new fingerprint has higher priority, replace
        if new_fp.source_priority.value < best_match.source_priority.value:
            # Remove old match and add new one
            old_hash = best_match.get_deduplication_hash()
            if old_hash in self.pattern_fingerprints:
                del self.pattern_fingerprints[old_hash]
            
            new_hash = new_fp.get_deduplication_hash()
            self.pattern_fingerprints[new_hash] = new_fp
            return None  # No conflict, we upgraded
        
        return best_match
    
    def _select_best_fuzzy_match(self, new_fp: PatternFingerprint,
                                matches: List[PatternFingerprint]) -> Optional[PatternFingerprint]:
        """Select best fuzzy match with quality scoring"""
        if not matches:
            return None
        
        # Score matches by priority and phonetic similarity
        scored_matches = []
        for match in matches:
            score = (5 - match.source_priority.value) + match.phonetic_similarity
            scored_matches.append((score, match))
        
        # Sort by score (higher is better)
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_match = scored_matches[0]
        new_score = (5 - new_fp.source_priority.value) + new_fp.phonetic_similarity
        
        # If new pattern scores better, replace
        if new_score > best_score:
            old_hash = best_match.get_deduplication_hash()
            if old_hash in self.pattern_fingerprints:
                del self.pattern_fingerprints[old_hash]
            
            new_hash = new_fp.get_deduplication_hash()
            self.pattern_fingerprints[new_hash] = new_fp
            return None
        
        return best_match
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (your existing approach enhanced)"""
        if not text:
            return ""
        
        # Convert to lowercase and strip
        normalized = text.lower().strip()
        
        # Remove common punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common articles and prefixes for better matching
        words = normalized.split()
        filtered_words = []
        
        skip_words = {'the', 'a', 'an', 'feat', 'featuring', 'ft', 'with'}
        
        for word in words:
            if word not in skip_words:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _get_source_priority(self, source_file: str) -> SourcePriority:
        """Determine source priority based on filename"""
        source_file_lower = source_file.lower()
        
        for pattern, priority in self.source_priorities.items():
            if pattern in source_file_lower:
                return priority
        
        return SourcePriority.FALLBACK
    
    def get_deduplication_summary(self) -> Dict:
        """Get comprehensive deduplication statistics"""
        total_patterns = self.dedup_stats['patterns_processed']
        total_duplicates = self.dedup_stats['patterns_duplicated']
        duplicate_rate = (total_duplicates / max(total_patterns, 1)) * 100
        
        return {
            'song_statistics': {
                'songs_processed': self.dedup_stats['songs_processed'],
                'songs_duplicated': self.dedup_stats['songs_duplicated'],
                'song_duplicate_rate': f"{(self.dedup_stats['songs_duplicated'] / max(self.dedup_stats['songs_processed'], 1)) * 100:.1f}%"
            },
            'pattern_statistics': {
                'patterns_processed': total_patterns,
                'patterns_duplicated': total_duplicates,
                'duplicate_rate': f"{duplicate_rate:.1f}%",
                'exact_duplicates': self.dedup_stats['exact_duplicates'],
                'fuzzy_duplicates': self.dedup_stats['fuzzy_duplicates'],
                'context_duplicates': self.dedup_stats['context_duplicates']
            },
            'quality_improvements': {
                'source_upgrades': self.dedup_stats['source_upgrades'],
                'source_conflicts_resolved': self.dedup_stats['source_conflicts']
            },
            'cross_file_analysis': {
                'patterns_across_multiple_files': len([p for p in self.cross_file_patterns.values() if len(p) > 1]),
                'most_duplicated_patterns': self._get_most_duplicated_patterns()
            }
        }
    
    def _get_most_duplicated_patterns(self, top_n: int = 10) -> List[Dict]:
        """Get patterns that appear most frequently across files"""
        pattern_counts = {}
        for pattern_text, sources in self.cross_file_patterns.items():
            if len(sources) > 1:
                pattern_counts[pattern_text] = len(sources)
        
        # Sort by frequency
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'pattern': pattern, 'file_count': count, 'sources': self.cross_file_patterns[pattern][:5]}
            for pattern, count in sorted_patterns[:top_n]
        ]
    
    def export_clean_patterns(self, output_file: str):
        """Export deduplicated patterns for database insertion"""
        clean_patterns = []
        
        for pattern_hash, fingerprint in self.pattern_fingerprints.items():
            clean_patterns.append({
                'pattern': fingerprint.pattern_text,
                'source_word': fingerprint.source_word,
                'target_word': fingerprint.target_word,
                'artist': fingerprint.artist_normalized,
                'song': fingerprint.song_normalized,
                'line_distance': fingerprint.line_distance,
                'phonetic_similarity': fingerprint.phonetic_similarity,
                'source_file': fingerprint.source_file,
                'source_priority': fingerprint.source_priority.name,
                'deduplication_hash': pattern_hash
            })
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'clean_patterns': clean_patterns,
                'deduplication_summary': self.get_deduplication_summary()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(clean_patterns):,} clean patterns to {output_file}")

# Integration example with the enhanced database processor
def integrate_with_database_processor():
    """Example of how to integrate with the enhanced database processor"""
    deduplicator = CrossFileDeduplicator()
    
    print("🔄 Cross-File Deduplication System Ready")
    print("Integration points:")
    print("  1. detect_song_duplicates() - Call before processing each song")
    print("  2. detect_pattern_duplicates() - Call before adding each pattern")
    print("  3. get_deduplication_summary() - Review cleaning effectiveness")
    print("  4. export_clean_patterns() - Export final clean dataset")
    
    return deduplicator

if __name__ == "__main__":
    # Demo the system
    demo_deduplicator = integrate_with_database_processor()
