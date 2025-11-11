#!/usr/bin/env python3
"""
Homophone detection module for expanding rhyme database.
Based on RhymeZone's approach using CMU Pronouncing Dictionary.

This module finds words with identical pronunciations but different spellings,
which can significantly expand our rhyme results.
"""

import nltk
from nltk.corpus import cmudict
from typing import Dict, List, Set, Tuple
import sqlite3
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rhyme_core.config import PrecisionConfig

# Download NLTK data if needed
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

class HomophoneDetector:
    """
    Detects homophones using CMU Pronouncing Dictionary.
    
    Homophones are words with identical pronunciations but different spellings.
    This can significantly expand our rhyme database by finding words we might
    have missed due to spelling differences.
    """
    
    def __init__(self, config: PrecisionConfig = None):
        """Initialize the homophone detector."""
        self.config = config or PrecisionConfig()
        self.prondict = cmudict.dict()
        self._pron_to_words = None
        self._homophones_cache = {}
    
    def _build_pronunciation_lookup(self) -> Dict[str, List[str]]:
        """Build reverse lookup: pronunciation -> list of words."""
        if self._pron_to_words is not None:
            return self._pron_to_words
        
        print("Building homophone lookup table...")
        pron_to_words = {}
        
        for word, pronunciations in self.prondict.items():
            for pron in pronunciations:
                # Convert pronunciation to string key
                pron_key = ' '.join(pron)
                if pron_key not in pron_to_words:
                    pron_to_words[pron_key] = []
                pron_to_words[pron_key].append(word)
        
        self._pron_to_words = pron_to_words
        print(f"Built homophone lookup with {len(pron_to_words)} unique pronunciations")
        return pron_to_words
    
    def get_homophones(self, word: str) -> List[str]:
        """
        Get all homophones for a given word.
        
        Args:
            word: The word to find homophones for
            
        Returns:
            List of homophones (words with same pronunciation)
        """
        word_lower = word.lower()
        
        # Check cache first
        if word_lower in self._homophones_cache:
            return self._homophones_cache[word_lower]
        
        # Build lookup if needed
        pron_to_words = self._build_pronunciation_lookup()
        
        # Find homophones
        homophones = []
        if word_lower in self.prondict:
            pronunciations = self.prondict[word_lower]
            for pron in pronunciations:
                pron_key = ' '.join(pron)
                if pron_key in pron_to_words:
                    # Get all words with this pronunciation, excluding the original
                    words_with_same_pron = [w for w in pron_to_words[pron_key] if w != word_lower]
                    homophones.extend(words_with_same_pron)
        
        # Remove duplicates and cache
        homophones = list(set(homophones))
        self._homophones_cache[word_lower] = homophones
        
        return homophones
    
    def get_all_homophone_sets(self) -> Dict[str, List[str]]:
        """
        Get all homophone sets from CMU dictionary.
        
        Returns:
            Dictionary mapping pronunciation to list of homophones
        """
        pron_to_words = self._build_pronunciation_lookup()
        
        # Filter to only sets with multiple words (actual homophones)
        homophone_sets = {
            pron: words for pron, words in pron_to_words.items() 
            if len(words) > 1
        }
        
        return homophone_sets
    
    def expand_rhyme_results_with_homophones(self, rhyme_results: List[Dict]) -> List[Dict]:
        """
        Expand rhyme results by adding homophones.
        
        Args:
            rhyme_results: List of rhyme result dictionaries
            
        Returns:
            Expanded list with homophones added
        """
        expanded_results = list(rhyme_results)  # Copy original results
        seen_words = {result['word'].lower() for result in rhyme_results}
        
        for result in rhyme_results:
            word = result['word']
            homophones = self.get_homophones(word)
            
            for homophone in homophones:
                if homophone.lower() not in seen_words:
                    # Create new result entry for homophone
                    homophone_result = result.copy()
                    homophone_result['word'] = homophone
                    homophone_result['source'] = 'homophone'
                    homophone_result['homophone_of'] = word
                    
                    expanded_results.append(homophone_result)
                    seen_words.add(homophone.lower())
        
        return expanded_results
    
    def get_homophone_stats(self) -> Dict[str, int]:
        """Get statistics about homophones in the database."""
        homophone_sets = self.get_all_homophone_sets()
        
        total_homophone_words = sum(len(words) for words in homophone_sets.values())
        total_sets = len(homophone_sets)
        
        return {
            'total_homophone_sets': total_sets,
            'total_homophone_words': total_homophone_words,
            'average_words_per_set': total_homophone_words / total_sets if total_sets > 0 else 0
        }

def test_homophone_detection():
    """Test the homophone detection functionality."""
    print("Testing Homophone Detection")
    print("=" * 40)
    
    detector = HomophoneDetector()
    
    # Test with some example words
    test_words = ['doorknob', 'table', 'sister', 'double', 'brother', 'night', 'knight']
    
    for word in test_words:
        homophones = detector.get_homophones(word)
        print(f"{word}: {homophones}")
    
    # Get overall stats
    stats = detector.get_homophone_stats()
    print(f"\nHomophone Statistics:")
    print(f"Total homophone sets: {stats['total_homophone_sets']}")
    print(f"Total homophone words: {stats['total_homophone_words']}")
    print(f"Average words per set: {stats['average_words_per_set']:.1f}")

if __name__ == "__main__":
    test_homophone_detection()



