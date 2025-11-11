#!/usr/bin/env python3
"""
Multi-word phrase generator for rhyming phrases.

This module generates multi-word phrases that rhyme with a target word,
similar to how RhymeZone generates phrases like "poor job", "spruce knob", "blue knob".
"""

import sqlite3
import random
from typing import List, Dict, Tuple, Set
# No need to import DEFAULTS since we'll pass the path directly

class MultiWordPhraseGenerator:
    """
    Generates multi-word rhyming phrases by combining words that rhyme with the target.
    
    Strategy:
    1. Find words that rhyme with the target (perfect, near-perfect, assonance)
    2. Find common adjectives, nouns, verbs that can modify/combine with those words
    3. Generate phrases like "poor job", "spruce knob", "blue knob"
    4. Score phrases based on frequency, semantic coherence, and rhyme quality
    """
    
    def __init__(self, db_path: str = "data/words_index.sqlite"):
        self.db_path = db_path
        self.common_adjectives = self._load_common_adjectives()
        self.common_nouns = self._load_common_nouns()
        self.common_verbs = self._load_common_verbs()
        self.common_prepositions = ['in', 'on', 'at', 'by', 'for', 'with', 'to', 'from', 'of', 'about']
        self.common_articles = ['a', 'an', 'the']
        self.common_determiners = ['this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their']
    
    def _load_common_adjectives(self) -> List[str]:
        """Load common adjectives from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Since we don't have pos column, use frequency and syllable count to guess adjectives
            # Common adjectives are usually 1-2 syllables and have moderate frequency
            cur.execute("""
                SELECT word FROM words 
                WHERE syls <= 2 AND zipf >= 2.0 AND zipf <= 6.0
                ORDER BY zipf DESC
                LIMIT 200
            """)
            
            adjectives = [row[0] for row in cur.fetchall()]
            conn.close()
            
            # Add some common adjectives that might not be in database
            common_adj = ['big', 'small', 'good', 'bad', 'new', 'old', 'hot', 'cold', 'fast', 'slow',
                         'high', 'low', 'long', 'short', 'wide', 'narrow', 'thick', 'thin', 'heavy', 'light',
                         'bright', 'dark', 'loud', 'quiet', 'smooth', 'rough', 'soft', 'hard', 'clean', 'dirty',
                         'fresh', 'stale', 'sweet', 'sour', 'bitter', 'salty', 'spicy', 'mild', 'rich', 'poor',
                         'young', 'old', 'happy', 'sad', 'angry', 'calm', 'nervous', 'brave', 'scared', 'proud',
                         'blue', 'red', 'green', 'yellow', 'black', 'white', 'gray', 'brown', 'pink', 'purple']
            
            # Combine and deduplicate
            all_adjectives = list(set(adjectives + common_adj))
            return all_adjectives[:300]  # Limit to 300 most common
            
        except Exception as e:
            print(f"Warning: Could not load adjectives from database: {e}")
            return ['big', 'small', 'good', 'bad', 'new', 'old', 'hot', 'cold', 'fast', 'slow']
    
    def _load_common_nouns(self) -> List[str]:
        """Load common nouns from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Since we don't have pos column, use frequency and syllable count to guess nouns
            # Common nouns are usually 1-2 syllables and have high frequency
            cur.execute("""
                SELECT word FROM words 
                WHERE syls <= 2 AND zipf >= 3.0 AND zipf <= 7.0
                ORDER BY zipf DESC
                LIMIT 200
            """)
            
            nouns = [row[0] for row in cur.fetchall()]
            conn.close()
            
            # Add some common nouns that might not be in database
            common_nouns = ['man', 'woman', 'child', 'person', 'people', 'friend', 'family', 'home', 'house',
                           'car', 'road', 'street', 'city', 'town', 'country', 'world', 'earth', 'sky', 'sun',
                           'moon', 'star', 'tree', 'flower', 'grass', 'water', 'fire', 'air', 'wind', 'rain',
                           'snow', 'ice', 'rock', 'stone', 'sand', 'dirt', 'mud', 'food', 'bread', 'meat',
                           'fish', 'chicken', 'beef', 'pork', 'milk', 'juice', 'coffee', 'tea', 'beer', 'wine',
                           'money', 'dollar', 'cent', 'job', 'work', 'time', 'day', 'night', 'week', 'month',
                           'year', 'book', 'paper', 'pen', 'pencil', 'computer', 'phone', 'television', 'radio',
                           'music', 'song', 'movie', 'game', 'sport', 'ball', 'team', 'player', 'coach', 'fan']
            
            # Combine and deduplicate
            all_nouns = list(set(nouns + common_nouns))
            return all_nouns[:300]  # Limit to 300 most common
            
        except Exception as e:
            print(f"Warning: Could not load nouns from database: {e}")
            return ['man', 'woman', 'child', 'person', 'people', 'friend', 'family', 'home', 'house']
    
    def _load_common_verbs(self) -> List[str]:
        """Load common verbs from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Since we don't have pos column, use frequency and syllable count to guess verbs
            # Common verbs are usually 1-2 syllables and have high frequency
            cur.execute("""
                SELECT word FROM words 
                WHERE syls <= 2 AND zipf >= 4.0 AND zipf <= 8.0
                ORDER BY zipf DESC
                LIMIT 200
            """)
            
            verbs = [row[0] for row in cur.fetchall()]
            conn.close()
            
            # Add some common verbs that might not be in database
            common_verbs = ['be', 'have', 'do', 'say', 'get', 'make', 'go', 'know', 'take', 'see',
                           'come', 'think', 'look', 'want', 'give', 'use', 'find', 'tell', 'ask', 'work',
                           'seem', 'feel', 'try', 'leave', 'call', 'move', 'play', 'turn', 'start', 'stop',
                           'help', 'show', 'hear', 'let', 'put', 'end', 'begin', 'keep', 'hold', 'bring',
                           'write', 'read', 'run', 'walk', 'sit', 'stand', 'lie', 'sleep', 'eat', 'drink',
                           'buy', 'sell', 'pay', 'cost', 'spend', 'save', 'lose', 'win', 'beat', 'hit',
                           'catch', 'throw', 'push', 'pull', 'lift', 'carry', 'drive', 'ride', 'fly', 'swim']
            
            # Combine and deduplicate
            all_verbs = list(set(verbs + common_verbs))
            return all_verbs[:300]  # Limit to 300 most common
            
        except Exception as e:
            print(f"Warning: Could not load verbs from database: {e}")
            return ['be', 'have', 'do', 'say', 'get', 'make', 'go', 'know', 'take', 'see']
    
    def generate_phrases(self, target_word: str, rhyme_words: List[str], max_phrases: int = 100) -> List[Dict]:
        """
        Generate multi-word phrases using the rhyme words.
        
        Args:
            target_word: The original word to rhyme with
            rhyme_words: List of words that rhyme with target_word
            max_phrases: Maximum number of phrases to generate
            
        Returns:
            List of phrase dictionaries with word, score, and metadata
        """
        phrases = []
        seen_phrases = set()
        
        # Strategy 1: Adjective + Noun phrases (e.g., "poor job", "blue knob")
        for rhyme_word in rhyme_words[:50]:  # Limit to top 50 rhyme words
            for adj in self.common_adjectives[:100]:  # Limit to top 100 adjectives
                phrase = f"{adj} {rhyme_word}"
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    score = self._score_phrase(phrase, target_word, rhyme_word, 'adj_noun')
                    phrases.append({
                        'word': phrase,
                        'score': score,
                        'type': 'adj_noun',
                        'base_word': rhyme_word,
                        'modifier': adj
                    })
        
        # Strategy 2: Noun + Noun phrases (e.g., "door knob", "blue knob")
        for rhyme_word in rhyme_words[:50]:
            for noun in self.common_nouns[:100]:
                phrase = f"{noun} {rhyme_word}"
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    score = self._score_phrase(phrase, target_word, rhyme_word, 'noun_noun')
                    phrases.append({
                        'word': phrase,
                        'score': score,
                        'type': 'noun_noun',
                        'base_word': rhyme_word,
                        'modifier': noun
                    })
        
        # Strategy 3: Verb + Noun phrases (e.g., "open job", "close knob")
        for rhyme_word in rhyme_words[:50]:
            for verb in self.common_verbs[:100]:
                phrase = f"{verb} {rhyme_word}"
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    score = self._score_phrase(phrase, target_word, rhyme_word, 'verb_noun')
                    phrases.append({
                        'word': phrase,
                        'score': score,
                        'type': 'verb_noun',
                        'base_word': rhyme_word,
                        'modifier': verb
                    })
        
        # Strategy 4: Preposition + Noun phrases (e.g., "in job", "on knob")
        for rhyme_word in rhyme_words[:50]:
            for prep in self.common_prepositions:
                phrase = f"{prep} {rhyme_word}"
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    score = self._score_phrase(phrase, target_word, rhyme_word, 'prep_noun')
                    phrases.append({
                        'word': phrase,
                        'score': score,
                        'type': 'prep_noun',
                        'base_word': rhyme_word,
                        'modifier': prep
                    })
        
        # Strategy 5: Determiner + Noun phrases (e.g., "the job", "my knob")
        for rhyme_word in rhyme_words[:50]:
            for det in self.common_determiners:
                phrase = f"{det} {rhyme_word}"
                if phrase not in seen_phrases:
                    seen_phrases.add(phrase)
                    score = self._score_phrase(phrase, target_word, rhyme_word, 'det_noun')
                    phrases.append({
                        'word': phrase,
                        'score': score,
                        'type': 'det_noun',
                        'base_word': rhyme_word,
                        'modifier': det
                    })
        
        # Sort by score and return top phrases
        phrases.sort(key=lambda x: x['score'], reverse=True)
        return phrases[:max_phrases]
    
    def _score_phrase(self, phrase: str, target_word: str, rhyme_word: str, phrase_type: str) -> float:
        """
        Score a phrase based on various factors.
        
        Args:
            phrase: The generated phrase
            target_word: Original target word
            rhyme_word: The rhyming word in the phrase
            phrase_type: Type of phrase (adj_noun, noun_noun, etc.)
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score for phrase type
        type_scores = {
            'adj_noun': 0.8,    # "poor job" - very natural
            'noun_noun': 0.7,   # "door knob" - natural
            'verb_noun': 0.6,   # "open job" - less natural
            'prep_noun': 0.5,   # "in job" - less natural
            'det_noun': 0.4     # "the job" - less natural
        }
        score += type_scores.get(phrase_type, 0.3)
        
        # Bonus for common words
        words = phrase.split()
        for word in words:
            if word in self.common_adjectives[:50]:
                score += 0.1
            elif word in self.common_nouns[:50]:
                score += 0.1
            elif word in self.common_verbs[:50]:
                score += 0.05
        
        # Bonus for alliteration (same first letter)
        if target_word[0].lower() == rhyme_word[0].lower():
            score += 0.2
        
        # Bonus for shorter phrases (more natural)
        if len(phrase.split()) == 2:
            score += 0.1
        elif len(phrase.split()) == 3:
            score += 0.05
        
        # Penalty for very long phrases
        if len(phrase.split()) > 3:
            score -= 0.1
        
        # Filter out unnatural combinations
        if self._is_unnatural_phrase(phrase, phrase_type):
            score *= 0.3  # Heavy penalty for unnatural phrases
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))
    
    def _is_unnatural_phrase(self, phrase: str, phrase_type: str) -> bool:
        """
        Check if a phrase is unnatural and should be filtered out.
        
        Args:
            phrase: The phrase to check
            phrase_type: Type of phrase
            
        Returns:
            True if the phrase is unnatural
        """
        words = phrase.split()
        
        # Filter out phrases with very short words (likely abbreviations)
        if any(len(word) <= 1 for word in words):
            return True
        
        # Filter out phrases with numbers or special characters
        if any(not word.isalpha() for word in words):
            return True
        
        # Filter out specific unnatural combinations
        unnatural_combinations = [
            # Adjective + Noun combinations that don't make sense
            ('big', 'able'), ('small', 'able'), ('good', 'able'), ('bad', 'able'),
            ('new', 'able'), ('old', 'able'), ('hot', 'able'), ('cold', 'able'),
            ('fast', 'able'), ('slow', 'able'), ('live', 'able'), ('without', 'able'),
            ('three', 'able'), ('proud', 'able'), ('very', 'able'), ('free', 'able'),
            ('own', 'able'), ('home', 'able'), ('until', 'able'), ('last', 'able'),
            ('full', 'able'), ('clean', 'able'), ('found', 'able'), ('rich', 'able'),
            ('narrow', 'able'), ('set', 'able'), ('house', 'able'), ('week', 'able'),
            ('where', 'able'), ('sure', 'able'),
            
            # Verb + Noun combinations that don't make sense
            ('be', 'able'), ('have', 'able'), ('do', 'able'), ('say', 'able'),
            ('get', 'able'), ('make', 'able'), ('go', 'able'), ('know', 'able'),
            
            # Other unnatural combinations
            ('the', 'able'), ('a', 'able'), ('an', 'able'),
            
            # Similar patterns for other common rhyme words
            ('big', 'trouble'), ('small', 'trouble'), ('good', 'trouble'), ('bad', 'trouble'),
            ('new', 'trouble'), ('old', 'trouble'), ('hot', 'trouble'), ('cold', 'trouble'),
            ('fast', 'trouble'), ('slow', 'trouble'), ('live', 'trouble'), ('without', 'trouble'),
            ('three', 'trouble'), ('proud', 'trouble'), ('very', 'trouble'), ('free', 'trouble'),
            ('own', 'trouble'), ('home', 'trouble'), ('until', 'trouble'), ('last', 'trouble'),
            ('full', 'trouble'), ('clean', 'trouble'), ('found', 'trouble'), ('rich', 'trouble'),
            ('narrow', 'trouble'), ('set', 'trouble'), ('house', 'trouble'), ('week', 'trouble'),
            ('where', 'trouble'), ('sure', 'trouble'),
        ]
        
        if len(words) == 2:
            if (words[0].lower(), words[1].lower()) in unnatural_combinations:
                return True
        
        return False
    
    def get_word_frequency(self, word: str) -> float:
        """Get word frequency from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT freq FROM words WHERE word = ?", (word.lower(),))
            result = cur.fetchone()
            conn.close()
            return result[0] if result else 0.0
        except:
            return 0.0
