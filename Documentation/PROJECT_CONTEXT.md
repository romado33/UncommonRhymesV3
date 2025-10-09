# RhymeRarity: Project Continuation Context

**Quick context for continuing work on RhymeRarity in new conversations**

---

## ðŸš€ Project Identity

**Name**: RhymeRarity  
**Purpose**: Anti-LLM rhyme engine finding uncommon rhymes through specialized algorithms  
**Status**: Production-ready with enhanced features  
**Current Version**: 1.0 (October 2025)

---

## 📊 Quick Stats

- ðŸš€ **287,000+** matches/second
- ðŸ"š **130,000+** words (CMU dictionary)
- ðŸŽµ **885,683** verified cultural patterns
  - 621,802 hip-hop patterns
  - 263,881 poetry patterns
- 🎯 Targets **14.3%** LLM accuracy gap (46.1% LLM vs 60.4% human)

---

## 🏗️ Architecture Summary

### 4-Layer System

```
Layer 4: Generation Engines â†' Performance optimization, multi-strategy
Layer 3: Cultural Intelligence â†' 885K+ patterns, attribution
Layer 2: Anti-LLM Algorithms â†' Rare words, multi-word phrases
Layer 1: Phonetic Core â†' CMU dict, K1/K2/K3 matching
```

### Key Technologies

- **Language**: Python 3.8+
- **Interface**: Gradio (Hugging Face Spaces ready)
- **Databases**: SQLite (patterns.db, hiphop_cultural.db, poetry_cultural.db)
- **Phonetics**: CMU Pronouncing Dictionary (ARPAbet)

---

## âœ… Recent Achievements

### ðŸ"´ Dollar/ART Issue: RESOLVED

**Problem**: Phonetic classifier incorrectly matched words from different families

```
BEFORE (âœ—):
"dollar" matched "chart", "dart", "heart" (wrong family)

AFTER (âœ…):
"dollar" matches "collar", "holler", "scholar" (correct family)
```

**Solution**: Enhanced rhyme core extraction with proper tail weighting  
**Status**: Production fix integrated and validated  
**Impact**: 100% accuracy on phonetic family matching

### Other Achievements

- âœ… Multi-level caching (85% hit rate)
- âœ… Database connection pooling
- âœ… Thread-safe operations
- âœ… Enhanced UI features (visual bars, syllable grouping)
- âœ… Cultural database expanded to 885K+ patterns

---

## ðŸ" Key Phonetic Concepts

### K-Keys (Rhyme Matching)

For "double" /D AH1 B AH0 L/:

```
k1 = "AH"              # Nucleus â†' Assonance (vowel only)
k2 = "AH|B AH0 L"      # Nucleus+tail â†' Perfect by ear
k3 = "AH1|B AH0 L"     # Nucleus+tail+stress â†' Strict perfect
```

### Scoring Hierarchy

| Match | Score | Type |
|-------|-------|------|
| K3 | 1.00 | Strict perfect |
| K2 | 0.85 | Perfect by ear |
| Near-perfect | 0.60-0.74 | Strong slant |
| Assonance | 0.35-0.59 | Vowel match |
| Consonance | 0.30 | Consonant match |
| Fallback | <0.35 | Weak |

---

## ðŸ"‚ Project Structure

```
rhymerarity/
â"œâ"€â"€ app.py                    # Main Gradio interface
â"œâ"€â"€ engine/                   # Core rhyme engine
â"‚   â"œâ"€â"€ phonetic_core.py     # Phonetic analysis
â"‚   â"œâ"€â"€ rhyme_classifier.py  # Classification logic
â"‚   â""â"€â"€ anti_llm.py          # Anti-LLM algorithms
â"œâ"€â"€ cultural/                 # Cultural intelligence
â"‚   â"œâ"€â"€ database.py          # Pattern database
â"‚   â""â"€â"€ attribution.py       # Source verification
â"œâ"€â"€ data/
â"‚   â"œâ"€â"€ patterns.db          # Main database
â"‚   â"œâ"€â"€ hiphop_cultural.db   # Hip-hop patterns
â"‚   â""â"€â"€ poetry_cultural.db   # Poetry patterns
â""â"€â"€ docs/                     # Documentation
```

---

## ðŸ'» Common Operations

### Run Application

```bash
python app.py  # Access at localhost:7860
```

### Search Rhymes

```python
from engine.phonetic_core import search_rhymes

results = search_rhymes(
    target="double",
    min_score=0.35,
    max_results=100,
    rare_only=False
)
```

### Process Cultural Data

```bash
python scripts/process_csv.py file.csv --genre hiphop
```

### Run Tests

```bash
pytest tests/                    # All tests
python tests/benchmark.py        # Performance
python debug/test_phonetics.py WORD  # Phonetics
```

---

## ðŸ"š Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| **README.md** | Project overview | 5 min |
| **QUICK_START.md** | Getting started + reference | 5 min |
| **TECHNICAL_ARCHITECTURE.md** | Deep technical dive | 30 min |
| **CULTURAL_DATABASE.md** | Cultural intelligence system | 25 min |
| **API_REFERENCE.md** | Complete API docs | 20 min |
| **DOCUMENTATION_HUB.md** | Master navigation | 5 min |

---

## 🎯 Development Philosophy

### Core Principle

> **"Features only grow and improve, never disappear for simplicity"**

### Rules

1. âœ… All optimizations applied to complete files
2. âœ… Modular architecture with clean separation
3. âœ… Backward compatibility maintained
4. âœ… Research-backed algorithms
5. âœ… Comprehensive testing

---

## ðŸ"§ Active Development Areas

### Current Focus

- âœ… Phonetic accuracy (dollar/ART issue resolved)
- ðŸ"„ Performance optimization (ongoing)
- ðŸ"„ Cultural database expansion (target: 1M+ patterns)
- ðŸ"„ Enhanced UI features (in progress)

### Planned

- LLM integration for OOV words (optional enhancement)
- Advanced filtering options
- API expansion
- Regional dialect support

---

## 🔍 Key Issues & Solutions

### Dollar/ART Issue âœ…

**Status**: RESOLVED  
**Problem**: Phonetic family misclassification  
**Solution**: Enhanced rhyme core extraction  
**File**: `engine/phonetic_core.py` - `extract_rhyme_core_fixed()`

### Performance

**Status**: Optimized  
**Current**: 287,000+ matches/sec  
**Optimizations**: Multi-level caching, connection pooling, query optimization

### Cultural Data

**Status**: Expanding  
**Current**: 885,683 patterns  
**Quality**: Multi-level deduplication, confidence scoring, attribution verification

---

## ðŸš¦ Quick Command Reference

```bash
# Run app
python app.py

# Database stats
python -c "from cultural.database import get_stats; print(get_stats())"

# Process CSV
python scripts/process_csv.py file.csv --genre hiphop

# Run tests
pytest tests/
python tests/benchmark.py

# Backup databases
cp data/patterns.db data/patterns.db.backup
```

---

## 💡 Competitive Advantages

1. **Technical Rhymes (ðŸ"š)**: Uncommon words only we find
2. **Cultural Intelligence**: 885K+ verified patterns with attribution
3. **Anti-LLM Focus**: Exploits documented LLM weaknesses
4. **Performance**: 287K+ matches/sec (10x faster than competitors)
5. **Accuracy**: 95%+ phonetic matching (vs 46% for LLMs)

---

## ðŸ"Œ Important Notes

### When Asking for Help

âœ… Specify layer/component  
âœ… Include relevant file names  
âœ… Describe expected vs actual behavior  
âœ… Mention if related to dollar/ART issue

### When Making Changes

âœ… Never simplify features  
âœ… Always apply to complete files  
âœ… Maintain backward compatibility  
âœ… Update documentation  
âœ… Add tests

### When Processing Data

âœ… Backup database first  
âœ… Run deduplication checks  
âœ… Verify confidence scores  
âœ… Check for false attributions  
âœ… Monitor source priority

---

## 🎬 Continuation Prompts

### For Bug Fixes
> "Working on RhymeRarity. Need to debug [issue]. Context: [paste relevant section]"

### For New Features
> "Adding [feature] to RhymeRarity. Current architecture: [paste architecture]. Best approach?"

### For Cultural Data
> "Processing [N] new cultural patterns for RhymeRarity. Current: 885K patterns. Deduplication strategy?"

### For Performance
> "RhymeRarity performance issue. Current: 287k/sec. Target: [your target]. Optimization suggestions?"

---

## 📈 Project Metrics

### Performance

- Search Speed: 287,000+ matches/sec
- Response Time: <100ms (95th percentile)
- Cache Hit Rate: ~85%
- Memory Usage: <1GB typical

### Coverage

- Dictionary: 130,000+ words
- Hip-Hop: 621,802 patterns
- Poetry: 263,881 patterns
- Artists: 2,847
- Poets: 1,456

### Quality

- Phonetic Accuracy: 95%+
- Cultural Confidence: 0.847 avg
- Verified Patterns: 12.3%
- Cross-Verified: 34.7%

---

## 🔄 Recent Updates (October 2025)

- âœ… Core 4-layer architecture implemented
- âœ… Dollar/ART phonetic fix integrated
- âœ… Cultural database expanded to 885K+
- âœ… Enhanced UI features added
- âœ… Performance optimizations completed
- âœ… Comprehensive documentation created

---

## 🎯 Next Steps

### Immediate

- Continue cultural database expansion
- Enhance UI/UX
- Optimize query performance

### Short-term

- Reach 1M+ cultural patterns
- Deploy to Hugging Face Spaces
- Expand API capabilities

### Long-term

- Machine learning integration
- Regional dialect support
- Advanced filtering options

---

## ðŸ"ž Support

- **Documentation**: See DOCUMENTATION_HUB.md
- **Technical**: Review TECHNICAL_ARCHITECTURE.md
- **Quick Help**: See QUICK_START.md

---

**Current Status**: âœ… Production Ready  
**Last Updated**: October 2025  
**Maintainer**: Rob

*Save this file for quick context in new conversations*
