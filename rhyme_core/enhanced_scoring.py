#!/usr/bin/env python3
"""
Enhanced scoring system to match RhymeZone's quality.

This module implements the K3/K2/K1 hierarchical scoring system:
- K3 (1.00): Exact stressed rime - perfect rhyme with same stress
- K2 (0.85): Perfect by ear - same sounds, stress-agnostic  
- Near-Perfect (0.60-0.74): Very close slant rhymes
- Assonance (0.35-0.59): Vowel rhymes with different consonants
- +0.10 bonus: Alliteration (matching onset)
- +0.05 bonus: Multi-syllable rhyme (2+ syllables match)
"""

import sqlite3
from typing import Dict, List, Tuple, Optional
from .phonetics import parse_pron, rhyme_tail, k_keys

class EnhancedScoringSystem:
    """
    Enhanced scoring system that matches RhymeZone's quality scoring.
    """
    
    def __init__(self, db_path: str = "data/words_index.sqlite"):
        self.db_path = db_path
    
    def calculate_rhyme_score(self, target_word: str, candidate_word: str, 
                            target_pron: str = None, candidate_pron: str = None,
                            enable_alliteration: bool = True) -> Dict:
        """
        Calculate comprehensive rhyme score matching RhymeZone's system.
        
        Args:
            target_word: The word to rhyme with
            candidate_word: The candidate rhyme word
            target_pron: Target pronunciation (optional, will lookup if not provided)
            candidate_pron: Candidate pronunciation (optional, will lookup if not provided)
            enable_alliteration: Whether to apply alliteration bonus
            
        Returns:
            Dictionary with score, category, and metadata
        """
        # Get pronunciations if not provided
        if not target_pron:
            target_pron = self._get_pronunciation(target_word)
        if not candidate_pron:
            candidate_pron = self._get_pronunciation(candidate_word)
        
        if not target_pron or not candidate_pron:
            return {'score': 0.0, 'category': 'no_pronunciation', 'metadata': {}}
        
        # Parse pronunciations
        target_phonemes = parse_pron(target_pron)
        candidate_phonemes = parse_pron(candidate_pron)
        
        if not target_phonemes or not candidate_phonemes:
            return {'score': 0.0, 'category': 'parse_error', 'metadata': {}}
        
        # Get phonetic keys
        target_k1, target_k2, target_k3 = k_keys(target_phonemes)
        candidate_k1, candidate_k2, candidate_k3 = k_keys(candidate_phonemes)
        
        # Calculate base score based on phonetic matching
        base_score, category, metadata = self._calculate_phonetic_score(
            target_k1, target_k2, target_k3,
            candidate_k1, candidate_k2, candidate_k3,
            target_phonemes, candidate_phonemes
        )
        
        # Apply bonuses
        final_score = base_score
        bonuses = []
        
        # Alliteration bonus (+0.10)
        if enable_alliteration and target_word[0].lower() == candidate_word[0].lower():
            final_score += 0.10
            bonuses.append('alliteration')
        
        # Multi-syllable rhyme bonus (+0.05)
        if self._has_multi_syllable_rhyme(target_phonemes, candidate_phonemes):
            final_score += 0.05
            bonuses.append('multi_syllable')
        
        # Ensure score is between 0.0 and 1.0
        final_score = max(0.0, min(1.0, final_score))
        
        metadata.update({
            'bonuses': bonuses,
            'target_keys': {'k1': target_k1, 'k2': target_k2, 'k3': target_k3},
            'candidate_keys': {'k1': candidate_k1, 'k2': candidate_k2, 'k3': candidate_k3},
            'target_pron': target_pron,
            'candidate_pron': candidate_pron
        })
        
        return {
            'score': final_score,
            'category': category,
            'metadata': metadata
        }
    
    def _calculate_phonetic_score(self, target_k1: str, target_k2: str, target_k3: str,
                                candidate_k1: str, candidate_k2: str, candidate_k3: str,
                                target_phonemes: List, candidate_phonemes: List) -> Tuple[float, str, Dict]:
        """
        Calculate base phonetic score based on K3/K2/K1 matching.
        
        Returns:
            Tuple of (score, category, metadata)
        """
        metadata = {}
        
        # K3 (1.00): Exact stressed rime - perfect rhyme with same stress
        if target_k3 == candidate_k3:
            metadata['match_type'] = 'k3_exact_stressed_rime'
            metadata['description'] = 'Perfect rhyme with same stress pattern'
            return 1.00, 'perfect', metadata
        
        # K2 (0.85): Perfect by ear - same sounds, stress-agnostic
        if target_k2 == candidate_k2:
            metadata['match_type'] = 'k2_perfect_by_ear'
            metadata['description'] = 'Same sounds, stress-agnostic'
            return 0.85, 'perfect', metadata
        
        # Near-Perfect (0.60-0.74): Very close slant rhymes
        if target_k1 == candidate_k1:
            # Check for near-perfect quality
            quality_score = self._assess_slant_rhyme_quality(target_phonemes, candidate_phonemes)
            if quality_score >= 0.7:
                metadata['match_type'] = 'k1_near_perfect'
                metadata['description'] = 'Very close slant rhyme'
                metadata['quality_score'] = quality_score
                return 0.70, 'near_perfect', metadata
            elif quality_score >= 0.6:
                metadata['match_type'] = 'k1_good_slant'
                metadata['description'] = 'Good slant rhyme'
                metadata['quality_score'] = quality_score
                return 0.65, 'near_perfect', metadata
        
        # Assonance (0.35-0.59): Vowel rhymes with different consonants
        if self._has_vowel_rhyme(target_phonemes, candidate_phonemes):
            assonance_score = self._assess_assonance_quality(target_phonemes, candidate_phonemes)
            if assonance_score >= 0.5:
                metadata['match_type'] = 'assonance_good'
                metadata['description'] = 'Good vowel rhyme'
                metadata['assonance_score'] = assonance_score
                return 0.55, 'assonance', metadata
            elif assonance_score >= 0.35:
                metadata['match_type'] = 'assonance_fair'
                metadata['description'] = 'Fair vowel rhyme'
                metadata['assonance_score'] = assonance_score
                return 0.45, 'assonance', metadata
        
        # No meaningful rhyme
        metadata['match_type'] = 'no_rhyme'
        metadata['description'] = 'No meaningful rhyme detected'
        return 0.0, 'no_rhyme', metadata
    
    def _assess_slant_rhyme_quality(self, target_phonemes: List, candidate_phonemes: List) -> float:
        """
        Assess the quality of a slant rhyme (K1 match).
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Get rhyme tails
        target_tail = rhyme_tail(target_phonemes)
        candidate_tail = rhyme_tail(candidate_phonemes)
        
        if not target_tail or not candidate_tail:
            return 0.0
        
        # Check for shared vowel sounds
        target_vowels = [p for p in target_tail if p[0] in 'AEIOU']
        candidate_vowels = [p for p in candidate_tail if p[0] in 'AEIOU']
        
        if not target_vowels or not candidate_vowels:
            return 0.0
        
        # Check if final vowels match
        if target_vowels[-1] == candidate_vowels[-1]:
            return 0.8  # High quality slant rhyme
        
        # Check for similar vowel sounds
        similar_vowels = {
            'AE': ['EH', 'AH'],
            'EH': ['AE', 'IH'],
            'IH': ['EH', 'IY'],
            'IY': ['IH'],
            'AO': ['AH', 'OW'],
            'OW': ['AO', 'UW'],
            'UW': ['OW'],
            'AH': ['AE', 'AO', 'UH'],
            'UH': ['AH']
        }
        
        target_final = target_vowels[-1]
        candidate_final = candidate_vowels[-1]
        
        if target_final in similar_vowels.get(candidate_final, []):
            return 0.6  # Medium quality slant rhyme
        
        return 0.3  # Low quality slant rhyme
    
    def _assess_assonance_quality(self, target_phonemes: List, candidate_phonemes: List) -> float:
        """
        Assess the quality of assonance (vowel rhyme).
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Get rhyme tails
        target_tail = rhyme_tail(target_phonemes)
        candidate_tail = rhyme_tail(candidate_phonemes)
        
        if not target_tail or not candidate_tail:
            return 0.0
        
        # Check for shared vowel sounds
        target_vowels = [p for p in target_tail if p[0] in 'AEIOU']
        candidate_vowels = [p for p in candidate_tail if p[0] in 'AEIOU']
        
        if not target_vowels or not candidate_vowels:
            return 0.0
        
        # Check if any vowels match
        shared_vowels = set(target_vowels) & set(candidate_vowels)
        if shared_vowels:
            return 0.5  # Good assonance
        
        # Check for similar vowel sounds
        similar_vowels = {
            'AE': ['EH', 'AH'],
            'EH': ['AE', 'IH'],
            'IH': ['EH', 'IY'],
            'IY': ['IH'],
            'AO': ['AH', 'OW'],
            'OW': ['AO', 'UW'],
            'UW': ['OW'],
            'AH': ['AE', 'AO', 'UH'],
            'UH': ['AH']
        }
        
        for target_vowel in target_vowels:
            for candidate_vowel in candidate_vowels:
                if target_vowel in similar_vowels.get(candidate_vowel, []):
                    return 0.3  # Fair assonance
        
        return 0.0  # No assonance
    
    def _has_vowel_rhyme(self, target_phonemes: List, candidate_phonemes: List) -> bool:
        """Check if words have any vowel rhyme."""
        target_tail = rhyme_tail(target_phonemes)
        candidate_tail = rhyme_tail(candidate_phonemes)
        
        if not target_tail or not candidate_tail:
            return False
        
        target_vowels = [p for p in target_tail if p[0] in 'AEIOU']
        candidate_vowels = [p for p in candidate_tail if p[0] in 'AEIOU']
        
        return bool(set(target_vowels) & set(candidate_vowels))
    
    def _has_multi_syllable_rhyme(self, target_phonemes: List, candidate_phonemes: List) -> bool:
        """Check if words have multi-syllable rhyme (2+ syllables match)."""
        target_tail = rhyme_tail(target_phonemes)
        candidate_tail = rhyme_tail(candidate_phonemes)
        
        if not target_tail or not candidate_tail:
            return False
        
        # Count matching syllables from the end
        matches = 0
        min_length = min(len(target_tail), len(candidate_tail))
        
        for i in range(1, min_length + 1):
            if target_tail[-i] == candidate_tail[-i]:
                matches += 1
            else:
                break
        
        return matches >= 2
    
    def _get_pronunciation(self, word: str) -> Optional[str]:
        """Get pronunciation from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT pron FROM words WHERE word = ?", (word.lower(),))
            result = cur.fetchone()
            conn.close()
            return result[0] if result else None
        except:
            return None



