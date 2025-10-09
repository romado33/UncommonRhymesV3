# RhymeRarity API Reference

## Overview

RhymeRarity provides both a Python API for direct integration and a REST API for web-based applications. This document covers all available endpoints, functions, and parameters.

---

## Table of Contents

1. [Python API](#python-api)
2. [REST API](#rest-api)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Python API

### Core Phonetic Functions

#### `get_phonemes(word: str) -> List[str]`

Get ARPAbet phonemes for a word from CMU dictionary.

**Parameters:**
- `word` (str): Word to get phonemes for

**Returns:**
- List[str]: ARPAbet phonemes, or empty list if word not found

**Example:**
```python
from engine.phonetic_core import get_phonemes

phonemes = get_phonemes("double")
# Returns: ['D', 'AH1', 'B', 'AH0', 'L']
```

---

#### `k_keys(phonemes: List[str]) -> Tuple[str, str, str]`

Generate K1, K2, K3 rhyme keys from phonemes.

**Parameters:**
- `phonemes` (List[str]): ARPAbet phonemes

**Returns:**
- Tuple[str, str, str]: (k1, k2, k3)

**Example:**
```python
from engine.phonetic_core import k_keys

phonemes = ['D', 'AH1', 'B', 'AH0', 'L']
k1, k2, k3 = k_keys(phonemes)
# Returns: ('AH', 'AH|B AH0 L', 'AH1|B AH0 L')
```

---

#### `search_rhymes(target: str, **kwargs) -> Dict`

Search for rhymes matching a target word.

**Parameters:**
- `target` (str): Target word to find rhymes for
- `min_score` (float, optional): Minimum similarity score (default: 0.35)
- `max_results` (int, optional): Maximum number of results (default: 100)
- `rare_only` (bool, optional): Only return rare words (zipf ≤ 6.0) (default: False)
- `include_cultural` (bool, optional): Include cultural patterns (default: True)
- `genre` (str, optional): Filter cultural patterns by genre ('hiphop', 'poetry', 'all') (default: 'all')
- `min_confidence` (float, optional): Minimum cultural pattern confidence (default: 0.6)

**Returns:**
- Dict with structure:
```python
{
    'target': str,
    'phonemes': List[str],
    'k1': str,
    'k2': str,
    'k3': str,
    'results': {
        'perfect': List[Dict],    # K3/K2 matches
        'near_perfect': List[Dict],  # Score 0.60-0.74
        'slant': List[Dict],      # Score 0.35-0.59
        'fallback': List[Dict]    # Score <0.35 (only if total < 5)
    },
    'cultural': List[Dict],       # Cultural patterns
    'stats': {
        'total_matches': int,
        'search_time_ms': float,
        'cache_hit': bool
    }
}
```

**Example:**
```python
from engine.phonetic_core import search_rhymes

results = search_rhymes(
    target="double",
    min_score=0.60,
    max_results=50,
    rare_only=True
)

for rhyme in results['results']['perfect']:
    print(f"{rhyme['word']}: {rhyme['score']}")
```

---

### Rhyme Classification Functions

#### `classify_rhyme(word1: str, word2: str) -> Dict`

Classify the relationship between two words.

**Parameters:**
- `word1` (str): First word
- `word2` (str): Second word

**Returns:**
- Dict with structure:
```python
{
    'type': str,           # 'perfect', 'near_perfect', 'slant', etc.
    'score': float,        # 0.0-1.0
    'pattern': str,        # 'K3', 'K2', 'K1', 'other'
    'details': {
        'k1_match': bool,
        'k2_match': bool,
        'k3_match': bool,
        'nucleus_similarity': float,
        'tail_similarity': float,
        'stress_alignment': float
    }
}
```

**Example:**
```python
from engine.rhyme_classifier import classify_rhyme

classification = classify_rhyme("double", "trouble")
# Returns: {'type': 'perfect', 'score': 1.0, 'pattern': 'K3', ...}
```

---

### Cultural Intelligence Functions

#### `get_cultural_patterns(target: str, **kwargs) -> List[Dict]`

Get cultural rhyme patterns for a target word.

**Parameters:**
- `target` (str): Target word
- `genre` (str, optional): 'hiphop', 'poetry', or 'all' (default: 'all')
- `min_confidence` (float, optional): Minimum confidence score (default: 0.6)
- `verified_only` (bool, optional): Only verified patterns (default: False)
- `limit` (int, optional): Maximum results (default: 100)

**Returns:**
- List[Dict] with structure:
```python
[
    {
        'target_rhyme': str,
        'rhyme_word': str,
        'artist': str,           # or 'poet' for poetry
        'song_title': str,       # or 'poem_title' for poetry
        'confidence_score': float,
        'verified': bool,
        'phonetic_pattern': str,  # 'K1', 'K2', 'K3'
        'distance': int,          # lines between rhymes (hip-hop)
        'rhyme_scheme': str       # ABAB, etc. (poetry)
    },
    ...
]
```

**Example:**
```python
from cultural.database import get_cultural_patterns

patterns = get_cultural_patterns(
    target="love",
    genre="hiphop",
    min_confidence=0.8,
    verified_only=True
)

for pattern in patterns:
    print(f"{pattern['artist']}: {pattern['rhyme_word']}")
```

---

#### `get_artist_stats(artist: str) -> Dict`

Get statistics for a specific artist or poet.

**Parameters:**
- `artist` (str): Artist/poet name

**Returns:**
```python
{
    'name': str,
    'genre': str,
    'pattern_count': int,
    'unique_targets': int,
    'unique_rhymes': int,
    'avg_confidence': float,
    'verified_count': int,
    'songs_count': int,
    'common_patterns': List[Dict],
    'favorite_rhymes': List[Tuple[str, str, int]]  # (target, rhyme, count)
}
```

**Example:**
```python
from cultural.database import get_artist_stats

stats = get_artist_stats("Eminem")
print(f"Total patterns: {stats['pattern_count']}")
print(f"Unique rhymes: {stats['unique_rhymes']}")
```

---

### Anti-LLM Functions

#### `detect_rare_words(candidates: List[str]) -> List[str]`

Identify words that LLMs typically miss.

**Parameters:**
- `candidates` (List[str]): List of candidate words

**Returns:**
- List[str]: Words classified as "rare" (zipf ≤ 6.0, not in Datamuse)

**Example:**
```python
from engine.anti_llm import detect_rare_words

candidates = ["trouble", "stubble", "gubble", "scrobble"]
rare = detect_rare_words(candidates)
# Returns: ["gubble", "scrobble"]
```

---

#### `get_challenge_rhymes(word: str) -> List[str]`

Get hardcoded rhymes for challenging words.

**Parameters:**
- `word` (str): Challenge word (e.g., "orange", "purple", "silver")

**Returns:**
- List[str]: Known rhymes including multi-word and archaic options

**Example:**
```python
from engine.anti_llm import get_challenge_rhymes

rhymes = get_challenge_rhymes("orange")
# Returns: ["door hinge", "four inch", "sporange", "Blorenge"]
```

---

## REST API

### Base URL

```
https://api.rhymerarity.com/v1
```

### Authentication

Include API key in header:
```
Authorization: Bearer YOUR_API_KEY
```

---

### Endpoints

#### `GET /search`

Search for rhymes.

**Parameters:**
- `word` (required): Target word
- `min_score` (optional): Minimum score (default: 0.35)
- `max_results` (optional): Maximum results (default: 100)
- `rare_only` (optional): Boolean (default: false)
- `include_cultural` (optional): Boolean (default: true)
- `genre` (optional): 'hiphop', 'poetry', 'all' (default: 'all')

**Example Request:**
```bash
curl "https://api.rhymerarity.com/v1/search?word=double&min_score=0.6&rare_only=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "target": "double",
  "phonemes": ["D", "AH1", "B", "AH0", "L"],
  "k1": "AH",
  "k2": "AH|B AH0 L",
  "k3": "AH1|B AH0 L",
  "results": {
    "perfect": [
      {
        "word": "trouble",
        "score": 1.0,
        "pattern": "K3",
        "phonemes": ["T", "R", "AH1", "B", "AH0", "L"],
        "zipf": 5.2,
        "syllables": 2
      }
    ],
    "near_perfect": [],
    "slant": [],
    "fallback": []
  },
  "cultural": [
    {
      "target_rhyme": "double",
      "rhyme_word": "trouble",
      "artist": "Eminem",
      "song_title": "Without Me",
      "confidence_score": 0.95
    }
  ],
  "stats": {
    "total_matches": 42,
    "search_time_ms": 12,
    "cache_hit": true
  }
}
```

---

#### `GET /phonemes/{word}`

Get phonemes for a word.

**Parameters:**
- `word` (required): Word to analyze

**Example Request:**
```bash
curl "https://api.rhymerarity.com/v1/phonemes/double" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "word": "double",
  "phonemes": ["D", "AH1", "B", "AH0", "L"],
  "syllables": 2,
  "stress_pattern": "1-0",
  "k1": "AH",
  "k2": "AH|B AH0 L",
  "k3": "AH1|B AH0 L"
}
```

---

#### `POST /classify`

Classify relationship between two words.

**Request Body:**
```json
{
  "word1": "double",
  "word2": "trouble"
}
```

**Example Request:**
```bash
curl -X POST "https://api.rhymerarity.com/v1/classify" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"word1": "double", "word2": "trouble"}'
```

**Example Response:**
```json
{
  "type": "perfect",
  "score": 1.0,
  "pattern": "K3",
  "details": {
    "k1_match": true,
    "k2_match": true,
    "k3_match": true,
    "nucleus_similarity": 1.0,
    "tail_similarity": 1.0,
    "stress_alignment": 1.0
  }
}
```

---

#### `GET /cultural/{artist}`

Get patterns for a specific artist.

**Parameters:**
- `artist` (required): Artist name
- `limit` (optional): Maximum results (default: 100)
- `min_confidence` (optional): Minimum confidence (default: 0.6)

**Example Request:**
```bash
curl "https://api.rhymerarity.com/v1/cultural/Eminem?limit=50&min_confidence=0.8" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "artist": "Eminem",
  "pattern_count": 47382,
  "patterns": [
    {
      "target_rhyme": "mom",
      "rhyme_word": "palm",
      "song_title": "Lose Yourself",
      "confidence_score": 0.95,
      "phonetic_pattern": "K2"
    },
    ...
  ],
  "stats": {
    "unique_targets": 8234,
    "unique_rhymes": 9876,
    "avg_confidence": 0.87,
    "songs_count": 342
  }
}
```

---

#### `POST /batch-search`

Search for multiple words in one request.

**Request Body:**
```json
{
  "words": ["double", "trouble", "bubble"],
  "min_score": 0.6,
  "max_results": 50
}
```

**Example Response:**
```json
{
  "results": {
    "double": { /* search results */ },
    "trouble": { /* search results */ },
    "bubble": { /* search results */ }
  },
  "stats": {
    "total_searches": 3,
    "total_time_ms": 45,
    "cached_results": 2
  }
}
```

---

#### `GET /stats`

Get system statistics.

**Example Request:**
```bash
curl "https://api.rhymerarity.com/v1/stats" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "database": {
    "total_words": 130147,
    "hiphop_patterns": 621802,
    "poetry_patterns": 263881,
    "verified_patterns": 109234
  },
  "performance": {
    "avg_search_time_ms": 15,
    "cache_hit_rate": 0.85,
    "uptime_seconds": 3600000
  },
  "api": {
    "requests_today": 15234,
    "requests_this_hour": 892
  }
}
```

---

## Authentication

### Getting an API Key

1. Register at https://rhymerarity.com/register
2. Verify your email
3. Generate API key in dashboard

### Using the API Key

**REST API:**
```bash
curl "https://api.rhymerarity.com/v1/search?word=double" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python SDK:**
```python
from rhymerarity import RhymeRarity

client = RhymeRarity(api_key="YOUR_API_KEY")
results = client.search("double")
```

---

## Rate Limiting

### Limits by Tier

| Tier | Requests/Hour | Requests/Day | Max Batch Size |
|------|---------------|--------------|----------------|
| Free | 100 | 1,000 | 10 |
| Basic | 1,000 | 10,000 | 50 |
| Pro | 10,000 | 100,000 | 200 |
| Enterprise | Unlimited | Unlimited | 1000 |

### Rate Limit Headers

Response includes headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1634567890
```

### Handling Rate Limits

**HTTP 429 Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 3600 seconds.",
  "retry_after": 3600
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found - Word not in dictionary |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Maintenance |

### Error Response Format

```json
{
  "error": "invalid_parameter",
  "message": "min_score must be between 0.0 and 1.0",
  "field": "min_score",
  "value": 1.5
}
```

### Common Errors

**Word Not Found:**
```json
{
  "error": "word_not_found",
  "message": "Word 'xyzabc' not found in CMU dictionary",
  "word": "xyzabc",
  "suggestions": ["xyz", "abc"]
}
```

**Invalid API Key:**
```json
{
  "error": "invalid_api_key",
  "message": "The provided API key is invalid or has been revoked"
}
```

**Rate Limit Exceeded:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Upgrade your plan for higher limits.",
  "current_tier": "free",
  "limit": 100,
  "retry_after": 3600
}
```

---

## Examples

### Python Examples

#### Basic Search
```python
from rhymerarity import RhymeRarity

client = RhymeRarity(api_key="YOUR_API_KEY")

# Simple search
results = client.search("double")

# Print perfect rhymes
for rhyme in results['results']['perfect']:
    print(f"{rhyme['word']}: {rhyme['score']}")
```

#### Advanced Search with Filters
```python
# Rare words only, high confidence cultural patterns
results = client.search(
    target="love",
    min_score=0.70,
    rare_only=True,
    include_cultural=True,
    genre="hiphop",
    min_confidence=0.85
)

# Process results
for pattern in results['cultural']:
    print(f"{pattern['artist']}: {pattern['rhyme_word']} "
          f"(confidence: {pattern['confidence_score']})")
```

#### Batch Processing
```python
words = ["love", "hate", "pain", "joy"]
results = client.batch_search(words, min_score=0.6)

for word, data in results['results'].items():
    print(f"\n{word}: {data['stats']['total_matches']} matches")
```

---

### JavaScript Examples

#### Using Fetch API
```javascript
const API_KEY = 'YOUR_API_KEY';
const BASE_URL = 'https://api.rhymerarity.com/v1';

async function searchRhymes(word) {
  const response = await fetch(
    `${BASE_URL}/search?word=${word}&min_score=0.6`,
    {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    }
  );
  
  const data = await response.json();
  return data;
}

// Usage
searchRhymes('double').then(results => {
  console.log(`Found ${results.stats.total_matches} rhymes`);
  results.results.perfect.forEach(rhyme => {
    console.log(`${rhyme.word}: ${rhyme.score}`);
  });
});
```

#### Using Axios
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://api.rhymerarity.com/v1',
  headers: {
    'Authorization': `Bearer ${process.env.RHYMERARITY_API_KEY}`
  }
});

// Search rhymes
client.get('/search', { params: { word: 'double', min_score: 0.6 } })
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error('Error:', error.response.data);
  });
```

---

### cURL Examples

#### Basic Search
```bash
curl "https://api.rhymerarity.com/v1/search?word=double" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Search with Filters
```bash
curl "https://api.rhymerarity.com/v1/search?word=love&min_score=0.7&rare_only=true&genre=hiphop" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Classify Words
```bash
curl -X POST "https://api.rhymerarity.com/v1/classify" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"word1": "double", "word2": "trouble"}'
```

#### Batch Search
```bash
curl -X POST "https://api.rhymerarity.com/v1/batch-search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "words": ["love", "hate", "pain"],
    "min_score": 0.6,
    "max_results": 50
  }'
```

---

## SDK Installation

### Python
```bash
pip install rhymerarity
```

### JavaScript/Node.js
```bash
npm install rhymerarity
```

### Ruby
```bash
gem install rhymerarity
```

---

## Webhooks (Enterprise Only)

### Event Types
- `pattern.added` - New cultural pattern added
- `word.processed` - New word added to dictionary
- `pattern.verified` - Pattern manually verified
- `artist.updated` - Artist statistics updated

### Webhook Payload
```json
{
  "event": "pattern.added",
  "timestamp": "2024-10-09T14:32:00Z",
  "data": {
    "target_rhyme": "love",
    "rhyme_word": "above",
    "artist": "Artist Name",
    "song_title": "Song Title",
    "confidence_score": 0.92
  }
}
```

---

## Support

- **Documentation**: https://docs.rhymerarity.com
- **API Status**: https://status.rhymerarity.com
- **Support Email**: api-support@rhymerarity.com
- **GitHub Issues**: https://github.com/rhymerarity/api/issues

---

*API Reference - v1.0 - October 2025*
