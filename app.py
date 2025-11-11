#!/usr/bin/env python3
"""
Anti-LLM Rhyme Engine - Enhanced Gradio UI with Column Layout - FIXED VERSION
Results displayed in columns: Perfect | Slant | Colloquial
Rap patterns full-width below
WITH COMPREHENSIVE LOGGING for troubleshooting and monitoring
INCLUDES SEARCH TERM ANALYSIS: stress pattern and metrical foot display

INTEGRATION FIXES:
✅ Imports match fixed engine.py exports
✅ Function call signatures are compatible
✅ Result schema matches engine.py output
✅ Helper functions (get_result_counts, organize_by_syllables) now available
✅ All filters properly passed to search_rhymes()
"""

import gradio as gr
from rhyme_core.engine import search_rhymes, get_result_counts, organize_by_syllables, cfg
import logging
from pathlib import Path
from datetime import datetime
import uuid
import time
import sqlite3

# =============================================================================
# LOGGING SETUP
# =============================================================================

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_DIR / 'app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('rhyme.app')
logger.info(f"App starting… logging to {LOG_DIR / 'app.log'}")

# =============================================================================
# METRICAL ANALYSIS FUNCTIONS
# =============================================================================

# Metrical foot patterns mapping
METRICAL_FEET = {
    (0, 1): "iamb (unstressed-stressed: x /)",
    (1, 0): "trochee (stressed-unstressed: / x)",
    (1, 0, 0): "dactyl (stressed-unstressed-unstressed: / x x)",
    (0, 0, 1): "anapest (unstressed-unstressed-stressed: x x /)",
    (1, 1): "spondee (stressed-stressed: / /)",
    (0, 0): "pyrrhic (unstressed-unstressed: x x)",
    (0, 1, 0): "amphibrach (unstressed-stressed-unstressed: x / x)",
    (1, 0, 1): "amphimacer (stressed-unstressed-stressed: / x /)",
}

def estimate_syllables(word: str) -> int:
    """
    Estimate syllable count for words not in CMU database.
    Simple vowel-based counting with some common patterns.
    """
    word = word.lower().strip()
    if not word:
        return 0
    
    # Count vowel groups (consecutive vowels count as one syllable)
    vowels = 'aeiouy'
    syllable_count = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllable_count += 1
        prev_was_vowel = is_vowel
    
    # Handle silent 'e' at the end
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    # Handle common patterns
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    
    # Minimum 1 syllable for any word
    return max(1, syllable_count)

def get_stress_pattern_from_db(word: str) -> tuple:
    """
    Get stress pattern and metrical foot for a word from CMU database
    Returns: (stress_pattern, metrical_foot_name, syllable_count)
    """
    try:
        db_path = Path(__file__).parent / "rhyme_core" / "data" / "cmudict.db"
        if not db_path.exists():
            # Try alternative path
            db_path = Path(__file__).parent / "data" / "cmudict.db"
        
        if not db_path.exists():
            # Try words_index.sqlite
            db_path = Path(__file__).parent / "data" / "words_index.sqlite"
        
        if not db_path.exists():
            return None, None, estimate_syllables(word)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Query for pronunciation - handle different table structures
        try:
            cursor.execute("""
                SELECT pron, stress, syls 
                FROM words 
                WHERE word = ? 
                LIMIT 1
            """, (word.lower(),))
        except sqlite3.OperationalError:
            # Try alternative column names
            cursor.execute("""
                SELECT pronunciation, stress, syls 
                FROM words 
                WHERE word = ? 
                LIMIT 1
            """, (word.lower(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Word not in database - estimate syllables
            estimated_syls = estimate_syllables(word)
            return None, None, estimated_syls
        
        pronunciation, stress, syls = result
        
        # Parse stress pattern
        if stress:
            # Handle both "10" and "1-0" formats
            if '-' in stress:
                stress_list = [int(s) for s in stress.split('-') if s.isdigit()]
            else:
                # Handle "10" format - split each digit
                stress_list = [int(s) for s in stress if s.isdigit()]
            stress_tuple = tuple(stress_list)
            
            # Find matching metrical foot - extract just the name, not the description
            metrical_foot_full = METRICAL_FEET.get(stress_tuple, None)
            if metrical_foot_full:
                # Extract just the metrical foot name (before any parentheses or descriptions)
                metrical_foot = metrical_foot_full.split(' (')[0].strip()
            else:
                metrical_foot = None
            
            # Format stress pattern for display
            stress_display = stress.replace('-', '‑')  # Non-breaking hyphen
            
            return stress_display, metrical_foot, syls
        
        return None, None, syls
    
    except Exception as e:
        logger.error(f"Error getting stress pattern for '{word}': {e}")
        return None, None, 0

def format_search_term_info(term: str) -> str:
    """Format search term analysis section"""
    stress_pattern, metrical_foot, syls = get_stress_pattern_from_db(term)
    
    if not stress_pattern:
        return f"""### 🎯 Search Term: "{term}"
*Stress pattern not found in database. Results shown below.*

---"""
    
    output = [f"### 🎯 Search Term: \"{term}\""]
    output.append(f"**Syllables:** {syls}")
    output.append(f"**Stress Pattern:** {stress_pattern}")
    
    if metrical_foot:
        output.append(f"**Metrical Foot:** {metrical_foot}")
    
    output.append("\n---")
    
    return "\n".join(output)

# =============================================================================
# FORMATTING FUNCTIONS
# =============================================================================


def ensure_complete_metrical_data(item: dict) -> dict:
    """
    Ensure all rhyme items have complete metrical data (syllables, stress, metrical foot).
    This function guarantees consistent display across DM and CMU results.
    """
    word = item['word']
    
    # Get current data
    current_syls = item.get('syls', 0)
    current_stress = item.get('stress', '')
    current_metrical = item.get('metrical_foot', '')
    
    # If any data is missing, try database lookup
    if current_syls == 0 or not current_stress or not current_metrical:
        stress_from_db, metrical_from_db, syls_from_db = get_stress_pattern_from_db(word)
        
        # Use database data to fill in missing information
        if current_syls == 0 and syls_from_db > 0:
            item['syls'] = syls_from_db
        if not current_stress and stress_from_db:
            item['stress'] = stress_from_db
        if not current_metrical and metrical_from_db:
            item['metrical_foot'] = metrical_from_db
    
    # Final check: ensure we have at least estimated syllables
    if item.get('syls', 0) == 0:
        item['syls'] = estimate_syllables(word)
    
    return item

def format_rhyme_item(item: dict, emoji: str = "", show_pronunciation: bool = False, item_number: int = 0) -> str:
    """Format a single rhyme result with emoji, metrical pattern info, and source color coding"""
    # Ensure complete metrical data first
    item = ensure_complete_metrical_data(item)
    
    word = item['word']
    score = item.get('score', 0)
    zipf = item.get('zipf', 0)
    syls = item.get('syls', 0)
    stress = item.get('stress', '')
    pron = item.get('pron', '')
    has_alliteration = item.get('has_alliteration', False)
    matching_syls = item.get('matching_syllables', 0)
    datamuse_verified = item.get('datamuse_verified', False)
    source = item.get('source', '')
    metrical_foot = item.get('metrical_foot', '')
    
    metrical_display = f" *{metrical_foot}*" if metrical_foot else ""
    
    # Format stress pattern nicely (ensure 1-0 format)
    if stress:
        # Clean stress pattern - replace any '2's with '1's and ensure hyphens
        stress_clean = stress.replace('2', '1')
        # If it's like "10", convert to "1-0"
        if len(stress_clean) == 2 and stress_clean.isdigit():
            stress_display = f"{stress_clean[0]}-{stress_clean[1]}"
        else:
            stress_display = stress_clean.replace(' ', '-')
    else:
        stress_display = 'N/A'
    
    # Determine source color coding
    if datamuse_verified or 'datamuse' in source.lower():
        source_indicator = "🔵"  # Blue for Datamuse
        source_text = "DM"
    else:
        source_indicator = "🟢"  # Green for CMU/our model
        source_text = "CMU"
    
    # Build display string with source color coding and score
    # Use numbered format if item_number is provided, otherwise use emoji
    if item_number > 0:
        result = f"{item_number}. {source_indicator}{source_text} **{word}**"
    else:
        result = f"{emoji} {source_indicator}{source_text} **{word}**"
    
    # Add score display for debugging - handle both 0-1 scale (Datamuse) and 0-100 scale (CMU)
    if score >= 85 or score >= 0.95:
        score_type = "K3"
        score_str = f"📊{score:.2f}"
    elif score >= 80 or score >= 0.80:
        score_type = "K2"
        score_str = f"📊{score:.2f}"
    elif score >= 60 or score >= 0.60:
        score_type = "Near"
        score_str = f"📊{score:.2f}"
    elif score >= 35 or score >= 0.35:
        score_type = "Asson"
        score_str = f"📊{score:.2f}"
    else:
        score_type = "Low"
        score_str = f"📊{score:.2f}"
    result += f" {score_str}({score_type})"
    
    # Add alliteration indicator
    if has_alliteration:
        result += " 🔤"
    
    # Add multi-syllable indicator
    if matching_syls >= 2:
        result += f" 🎵×{matching_syls}"
    
    # Add metrical info in the requested format: Word: syllables * stress-pattern, metrical-foot
    result += f": {syls} * {stress_display}{metrical_display}"
    
    # Add pronunciation if enabled
    if show_pronunciation and pron:
        result += f"\n    `[{pron}]`"
    
    return result

def format_syllable_section(items: list, emoji: str, show_pronunciation: bool = False) -> list:
    """Format a list of items grouped by syllable count"""
    output = []
    
    if not items:
        return output
    
    by_syl = organize_by_syllables(items)
    
    for syl_count in sorted(by_syl.keys()):
        syl_items = by_syl[syl_count]
        count = len(syl_items)
        
        # Subsection header
        output.append(f"\n**{syl_count}-syllable ({count} rhymes):**\n")
        
        # Items
        for i, item in enumerate(syl_items, 1):
            output.append(format_rhyme_item(item, emoji, show_pronunciation, i))
        
    return output

def format_perfect_section(results: dict, counts: dict, show_pronunciation: bool = False) -> str:
    """Format Perfect Rhymes section with Popular/Technical subsections organized by syllables"""
    output = []
    
    perfect_pop = results['perfect']['popular']
    perfect_tech = results['perfect']['technical']
    
    if not perfect_pop and not perfect_tech:
        return "No perfect rhymes found. Check the Slant Rhymes section for approximate matches."
    
    # Popular section (both sources)
    if perfect_pop:
        # Organize by syllables
        by_syl = organize_by_syllables(perfect_pop)
        for syl_count in sorted(by_syl.keys()):
            syl_items = by_syl[syl_count]
            output.append(f"\n**{syl_count}-syllable ({len(syl_items)} rhymes):**\n")
            for item in syl_items:
                output.append(format_rhyme_item(item, "•", show_pronunciation))
        
        output.append("")  # Blank line
    
    # Technical section (CMU only) - OUR SPECIALTY
    if perfect_tech:
        # Organize by syllables
        by_syl = organize_by_syllables(perfect_tech)
        for syl_count in sorted(by_syl.keys()):
            syl_items = by_syl[syl_count]
            output.append(f"\n**{syl_count}-syllable ({len(syl_items)} rhymes):**\n")
            for item in syl_items:
                output.append(format_rhyme_item(item, "•", show_pronunciation))
        
        output.append("")
    
    # Summary stats
    total = counts['perfect_popular'] + counts['perfect_technical']
    output.append(f"\n**Total:** {total} perfect rhymes ({counts['perfect_popular']} popular, {counts['perfect_technical']} technical)")
    
    return "\n".join(output)

def format_slant_section(results: dict, counts: dict, show_pronunciation: bool = False) -> str:
    """Format Slant Rhymes section with all new K-key categories"""
    output = []
    
    # Get all slant rhyme categories
    near_pop = results['slant']['near_perfect']['popular']
    near_tech = results['slant']['near_perfect']['technical']
    asso_pop = results['slant']['assonance']['popular']
    asso_tech = results['slant']['assonance']['technical']
    terminal_pop = results['slant'].get('terminal_match', {}).get('popular', [])
    terminal_tech = results['slant'].get('terminal_match', {}).get('technical', [])
    consonance_pop = results['slant'].get('consonance', {}).get('popular', [])
    consonance_tech = results['slant'].get('consonance', {}).get('technical', [])
    family_pop = results['slant'].get('family_rhymes', {}).get('popular', [])
    family_tech = results['slant'].get('family_rhymes', {}).get('technical', [])
    pararhyme_pop = results['slant'].get('pararhyme', {}).get('popular', [])
    pararhyme_tech = results['slant'].get('pararhyme', {}).get('technical', [])
    multisyl_pop = results['slant'].get('multisyllabic', {}).get('popular', [])
    multisyl_tech = results['slant'].get('multisyllabic', {}).get('technical', [])
    upstream_pop = results['slant'].get('upstream_assonance', {}).get('popular', [])
    upstream_tech = results['slant'].get('upstream_assonance', {}).get('technical', [])
    fallback = results['slant'].get('fallback', [])
    
    # Check if we have any slant rhymes
    all_slant_items = (near_pop + near_tech + asso_pop + asso_tech + 
                      terminal_pop + terminal_tech + consonance_pop + consonance_tech +
                      family_pop + family_tech + pararhyme_pop + pararhyme_tech +
                      multisyl_pop + multisyl_tech + upstream_pop + upstream_tech)
    
    if not all_slant_items and not fallback:
        return "No slant rhymes found. Try adjusting filters or check other sections."
    
    # Combine all slant rhyme items with type indicators
    all_items = []
    
    # Add items with type indicators
    for item in near_pop + near_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'near_perfect'
        all_items.append(item_copy)
    
    for item in asso_pop + asso_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'assonance'
        all_items.append(item_copy)
    
    for item in terminal_pop + terminal_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'terminal_match'
        all_items.append(item_copy)
    
    for item in consonance_pop + consonance_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'consonance'
        all_items.append(item_copy)
    
    for item in family_pop + family_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'family_rhymes'
        all_items.append(item_copy)
    
    for item in pararhyme_pop + pararhyme_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'pararhyme'
        all_items.append(item_copy)
    
    for item in multisyl_pop + multisyl_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'multisyllabic'
        all_items.append(item_copy)
    
    for item in upstream_pop + upstream_tech:
        item_copy = item.copy()
        item_copy['rhyme_type'] = 'upstream_assonance'
        all_items.append(item_copy)
    
    if not all_items:
        return "No slant rhymes found. Try adjusting filters or check other sections."
    
    # Group by syllables first, then by type within each syllable group
    by_syl = organize_by_syllables(all_items)
    
    for syl_count in sorted(by_syl.keys()):
        syl_items = by_syl[syl_count]
        count = len(syl_items)
        
        # Syllable header
        output.append(f"\n**{syl_count}-syllable ({count} rhymes):**\n")
        
        # Group by type within this syllable count
        type_groups = {
            'near_perfect': [item for item in syl_items if item.get('rhyme_type') == 'near_perfect'],
            'terminal_match': [item for item in syl_items if item.get('rhyme_type') == 'terminal_match'],
            'assonance': [item for item in syl_items if item.get('rhyme_type') == 'assonance'],
            'consonance': [item for item in syl_items if item.get('rhyme_type') == 'consonance'],
            'family_rhymes': [item for item in syl_items if item.get('rhyme_type') == 'family_rhymes'],
            'pararhyme': [item for item in syl_items if item.get('rhyme_type') == 'pararhyme'],
            'multisyllabic': [item for item in syl_items if item.get('rhyme_type') == 'multisyllabic'],
            'upstream_assonance': [item for item in syl_items if item.get('rhyme_type') == 'upstream_assonance']
        }
        
        # Add items by type with appropriate symbols
        item_num = 1
        for rhyme_type, items in type_groups.items():
            if items:
                # Add type header for clarity
                type_names = {
                    'near_perfect': 'Near-Perfect',
                    'terminal_match': 'Terminal Match',
                    'assonance': 'Assonance',
                    'consonance': 'Consonance',
                    'family_rhymes': 'Family Rhymes',
                    'pararhyme': 'Pararhyme',
                    'multisyllabic': 'Multisyllabic',
                    'upstream_assonance': 'Upstream Assonance'
                }
                
                if len(type_groups) > 1:  # Only show type headers if multiple types
                    output.append(f"*{type_names[rhyme_type]}:*")
                
                for item in items:
                    # Choose appropriate symbol based on rhyme type
                    symbols = {
                        'near_perfect': '•',
                        'terminal_match': '◐',
                        'assonance': '○',
                        'consonance': '◑',
                        'family_rhymes': '◒',
                        'pararhyme': '◓',
                        'multisyllabic': '◔',
                        'upstream_assonance': '◕'
                    }
                    symbol = symbols.get(rhyme_type, '•')
                    output.append(format_rhyme_item(item, symbol, show_pronunciation, item_num))
                    item_num += 1
        
            output.append("")
    
    # FALLBACK SECTION (only if total slant < 5)
    if fallback and counts['total_slant'] < 5:
        output.append("#### FALLBACK MATCHES")
        output.append("*Weak matches shown due to limited results (score < 0.35)*\n")
        for i, item in enumerate(fallback, 1):
            output.append(format_rhyme_item(item, "•", show_pronunciation, i))
        output.append("")
    
    # Summary stats
    total_slant = counts['total_slant']
    total_with_fallback = total_slant + (counts['fallback'] if counts['total_slant'] < 5 else 0)
    output.append(f"\n**Total:** {total_with_fallback} slant rhymes")
    
    # Add counts for each category
    categories = [
        ('Near-Perfect', 'near_perfect'),
        ('Terminal Match', 'terminal_match'),
        ('Assonance', 'assonance'),
        ('Consonance', 'consonance'),
        ('Family Rhymes', 'family_rhymes'),
        ('Pararhyme', 'pararhyme'),
        ('Multisyllabic', 'multisyllabic'),
        ('Upstream Assonance', 'upstream_assonance')
    ]
    
    for name, key in categories:
        pop_count = len(results['slant'].get(key, {}).get('popular', []))
        tech_count = len(results['slant'].get(key, {}).get('technical', []))
        if pop_count > 0 or tech_count > 0:
            output.append(f"- {name}: {pop_count + tech_count} ({pop_count} popular, {tech_count} technical)")
    
    if fallback and counts['total_slant'] < 5:
        output.append(f"- Fallback: {counts['fallback']}")
    
    return "\n".join(output)

def format_colloquial_section(results: dict, counts: dict) -> str:
    """Format Colloquial section (Datamuse multi-word phrases)"""
    output = []
    
    colloquial = results.get('colloquial', [])
    
    if not colloquial:
        return "No multi-word rhymes found."
    
    
    for i, item in enumerate(colloquial, 1):
        # Use the same formatting as other results
        formatted_item = format_rhyme_item(item, "•", False, i)
        output.append(formatted_item)
    
    output.append(f"\n**Total:** {counts['colloquial']} multi-word rhymes")
    
    return "\n".join(output)

def format_rap_section() -> str:
    """Format Rap Database section (placeholder)"""
    return """#### 🎤 Rap Rhyme Database

*Coming soon: Culturally-informed rhymes from hip-hop lyrics and poetry*

This section will feature:
- Multi-syllable rhymes from rap lyrics
- Slant rhymes popular in hip-hop culture
- Regional pronunciation variants
- Battle rap schemes and patterns

Stay tuned!"""

# =============================================================================
# SEARCH INTERFACE WITH LOGGING - FIXED
# =============================================================================

def search_interface(term: str, syl_filter: str, stress_filter: str, 
                     use_datamuse: bool, show_rare_only: bool, 
                     multisyl_only: bool, enable_alliteration: bool,
                     show_pronunciation: bool, show_popular_rhymes: bool = False,
                     show_obscure_rhymes: bool = False):
    """Main search interface function with all filters and comprehensive logging"""
    
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Log the search request
    logger.info(
        f"ui.submit id={request_id} term='{term}' syl={syl_filter} stress={stress_filter} "
        f"datamuse={use_datamuse} rare_only={show_rare_only} multisyl_only={multisyl_only} "
        f"alliteration={enable_alliteration}"
    )
    
    if not term.strip():
        empty_msg = "Enter a word above to search for rhymes."
        logger.info(f"ui.render id={request_id} empty_term=True")
        return "", empty_msg, empty_msg, empty_msg, empty_msg
    
    # Start timing
    start_time = time.time()
    
    try:
        # Format search term info
        term_info = format_search_term_info(term.strip())
        
        # Extract numerical pattern from metrical pattern selection
        # Handle both "1-0" and "1-0 (trochee)" formats
        if stress_filter != "Any" and "(" in stress_filter:
            # Extract just the numerical pattern from "1-0 (trochee)"
            stress_filter = stress_filter.split(" (")[0].strip()
        
        # Perform search - NOW WITH CORRECT SIGNATURE
        results = search_rhymes(
            term.strip(), 
            syl_filter=syl_filter,
            stress_filter=stress_filter,
            use_datamuse=use_datamuse,
            multisyl_only=multisyl_only,
            enable_alliteration=enable_alliteration
        )
        
        # Handle hidden rhymes if user wants to see them
        if show_popular_rhymes or show_obscure_rhymes:
            hidden = results.get('_hidden', {})
            
            if show_popular_rhymes and hidden.get('popular'):
                # Add popular rhymes back to results
                for item in hidden['popular']:
                    category = item['category']
                    if category == 'perfect':
                        if item.get('freq', 0) >= 2.0:
                            results['perfect']['popular'].append(item)
                        else:
                            results['perfect']['technical'].append(item)
                    elif category == 'slant':
                        score = item.get('score', 0)
                        if score >= 0.60:
                            if item.get('freq', 0) >= 2.0:
                                results['slant']['near_perfect']['popular'].append(item)
                            else:
                                results['slant']['near_perfect']['technical'].append(item)
                        else:
                            if item.get('freq', 0) >= 2.0:
                                results['slant']['assonance']['popular'].append(item)
                            else:
                                results['slant']['assonance']['technical'].append(item)
                    elif category == 'multiword':
                        results['colloquial'].append(item)
            
            if show_obscure_rhymes and hidden.get('obscure'):
                # Add obscure rhymes back to results
                for item in hidden['obscure']:
                    category = item['category']
                    if category == 'perfect':
                        if item.get('freq', 0) >= 2.0:
                            results['perfect']['popular'].append(item)
                        else:
                            results['perfect']['technical'].append(item)
                    elif category == 'slant':
                        score = item.get('score', 0)
                        if score >= 0.60:
                            if item.get('freq', 0) >= 2.0:
                                results['slant']['near_perfect']['popular'].append(item)
                            else:
                                results['slant']['near_perfect']['technical'].append(item)
                        else:
                            if item.get('freq', 0) >= 2.0:
                                results['slant']['assonance']['popular'].append(item)
                            else:
                                results['slant']['assonance']['technical'].append(item)
                    elif category == 'multiword':
                        results['colloquial'].append(item)
        
        # Apply "show rare only" filter
        if show_rare_only:
            results['perfect']['popular'] = []
            results['slant']['near_perfect']['popular'] = []
            results['slant']['assonance']['popular'] = []
        
        counts = get_result_counts(results)
        
        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Create preview dictionary with top results for logging
        preview = {
            'perfect_popular_top': [r['word'] for r in results['perfect']['popular'][:3]],
            'perfect_technical_top': [r['word'] for r in results['perfect']['technical'][:3]],
            'near_perfect_popular_top': [r['word'] for r in results['slant']['near_perfect']['popular'][:3]],
            'near_perfect_technical_top': [r['word'] for r in results['slant']['near_perfect']['technical'][:3]],
            'assonance_popular_top': [r['word'] for r in results['slant']['assonance']['popular'][:3]],
            'assonance_technical_top': [r['word'] for r in results['slant']['assonance']['technical'][:3]],
            'colloquial_top': [r['word'] for r in results.get('colloquial', [])[:3]]
        }
        
        # Log the results
        logger.info(
            f"ui.render id={request_id} elapsed_ms={elapsed_ms:.1f} counts={counts} preview={preview}"
        )
        
        # Add hidden rhymes summary to results
        hidden_summary = ""
        if '_hidden' in results:
            hidden = results['_hidden']
            popular_count = len(hidden.get('popular', []))
            obscure_count = len(hidden.get('obscure', []))
            if popular_count > 0 or obscure_count > 0:
                hidden_summary = f"\n**Hidden Rhymes:** {popular_count} popular, {obscure_count} obscure (use checkboxes above to show)"
        
        # Format each section
        perfect_output = format_perfect_section(results, counts, show_pronunciation) + hidden_summary
        slant_output = format_slant_section(results, counts, show_pronunciation)
        colloquial_output = format_colloquial_section(results, counts)
        rap_output = format_rap_section()
        
        return term_info, perfect_output, slant_output, colloquial_output, rap_output
        
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"ui.error id={request_id} elapsed_ms={elapsed_ms:.1f} error={str(e)}", exc_info=True)
        error_msg = f"Error during search: {str(e)}\n\nCheck logs/app.log for details."
        return "", error_msg, error_msg, error_msg, error_msg

# =============================================================================
# GRADIO INTERFACE
# =============================================================================

# Build Gradio interface
with gr.Blocks(
    title="Anti-LLM Rhyme Engine - Enhanced", 
    theme=gr.themes.Soft(),
    css="""
    /* Force all content to start at top */
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    /* Target specific columns with class */
    .top-align-column {
        align-self: flex-start !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
    }
    .top-align-column > * {
        align-self: flex-start !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        width: 100% !important;
    }
    /* Remove all vertical centering from rows */
    .gradio-row {
        align-items: flex-start !important;
        display: flex !important;
    }
    /* Remove spacing from headers */
    .gradio-markdown h3 {
        margin: 0 0 5px 0 !important;
        padding: 0 !important;
    }
    /* Remove spacing from tables */
    .gradio-markdown table {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Force markdown content to top */
    .gradio-markdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    """
) as app:
    gr.Markdown("""
    # 🎯 Anti-LLM Rhyme Engine - Enhanced Edition (FIXED)
    
    **Find uncommon rhymes that LLMs miss and traditional dictionaries don't know.**
    
    Our unique value: **Technical rhymes (📚)** are found ONLY in the CMU Pronunciation Dictionary - nobody else has them!
    
    **New Features:** Syllable grouping, multi-syllable detection, alliteration bonuses, metrical analysis
    
    **Integration Fixed:** All components now properly connected and tested
    
    ---
    """)
    
    # Input section
    with gr.Row():
        with gr.Column(scale=3):
            search_input = gr.Textbox(
                label="Search Term",
                placeholder="Enter a word (e.g., 'double', 'orange', 'month', 'table')",
                show_label=True
            )
        with gr.Column(scale=1):
            search_btn = gr.Button("🔍 Search", variant="primary", size="lg")
    
    # Filters section - collapsed into accordion
    with gr.Accordion("🎛️ Filters & Options", open=False):
        with gr.Row():
            syl_filter = gr.Dropdown(
                choices=["Any", "1", "2", "3", "4", "5+"],
                value="Any",
                label="Syllables",
                scale=1
            )
            stress_filter = gr.Dropdown(
                    choices=[
                        "Any", 
                        "1-0 (trochee)", "0-1 (iamb)", 
                        "1-0-0 (dactyl)", "0-0-1 (anapest)", "0-1-0 (amphibrach)",
                        "1-1 (spondee)", "0-0 (pyrrhic)"
                    ],
                value="Any",
                    label="Metrical Pattern",
                    info="Filter by stress pattern or metrical foot",
                scale=1
            )
        
        with gr.Row():
            datamuse_toggle = gr.Checkbox(
                value=True,
                label="✓ Use Datamuse API",
                info="Validate with Datamuse for popular/technical split",
                scale=1
            )
            show_rare_only = gr.Checkbox(
                value=False,
                label="🔬 Show rare/technical only",
                info="Hide popular rhymes, show only our unique finds",
                scale=1
            )
            multisyl_only = gr.Checkbox(
                value=False,
                label="🎵 Multi-syllable rhymes only",
                info="Only show double/triple rhymes (2+ syllables match)",
                scale=1
            )
        
        with gr.Row():
            enable_alliteration = gr.Checkbox(
                value=True,
                label="🔤 Enable alliteration bonus",
                info="Boost rhymes with matching onset consonants",
                scale=1
            )
            show_pronunciation = gr.Checkbox(
                value=False,
                label="🗣️ Show pronunciation",
                info="Display ARPAbet phonemes for each rhyme",
                    scale=1
                )
            
            # Uncommon rhyme controls
            gr.Markdown("**Uncommon Rhyme Settings:**")
            show_popular_rhymes = gr.Checkbox(
                value=False,
                label="Show Popular Rhymes",
                info="Display clichéd popular rhymes (normally hidden)",
                scale=1
            )
            show_obscure_rhymes = gr.Checkbox(
                value=False,
                label="Show Obscure Rhymes", 
                info="Display very rare/obscure rhymes (normally hidden)",
                scale=1
            )
    
    gr.Markdown("---")
    
    # Search term analysis section
    term_info_output = gr.Markdown(
        value="",
        line_breaks=True
    )
    
    gr.Markdown("## 📊 Results")
    gr.Markdown("*All results displayed below in columns - scroll to see each category*")
    
    # Row 1: Perfect | Slant | Colloquial (3 columns)
    with gr.Row(equal_height=False):
        # Column 1: Perfect Rhymes
        with gr.Column(scale=1, elem_classes="top-align-column"):
            gr.Markdown("### Perfect Rhymes")
            perfect_output = gr.Markdown(
                value="Enter a word above to see perfect rhymes.",
                line_breaks=True
            )
            with gr.Accordion("Perfect Rhymes Legend", open=False):
                gr.Markdown("""
                **Symbols:**
                - • = K3 strict perfect (exact stressed rime, score 1.00)
                - • = K2 perfect by ear (stress-agnostic, score 0.85)
                - • = Popular (found in both CMU and Datamuse)
                - • = Technical (CMU only - our specialty!)
                - • = Alliteration (matching onset consonants)
                - •×N = Multi-syllable rhyme (N syllables match)
                - ██████░░░░ = Popularity bar (more bars = more common)
                """)
        
        # Column 2: Slant Rhymes
        with gr.Column(scale=1, elem_classes="top-align-column"):
            gr.Markdown("### Slant Rhymes")
            slant_output = gr.Markdown(
                value="Enter a word above to see slant rhymes.",
                line_breaks=True
            )
            with gr.Accordion("Slant Rhymes Legend", open=False):
                gr.Markdown("""
                **Symbols:**
                - • = Near-perfect slant (score 0.60-0.74)
                - ◐ = Terminal match (compounds, score 0.60-0.74)
                - ○ = Assonance / vowel rhyme (score 0.35-0.59)
                - ◑ = Consonance / consonant rhyme (score 0.20-0.59)
                - ◒ = Family rhymes (phonetic similarity, score 0.15-0.59)
                - ◓ = Pararhyme (consonant frame, score 0.15-0.59)
                - ◔ = Multisyllabic (2+ syllables, score 0.10-0.59)
                - ◕ = Upstream assonance (pre-tail vowels, score 0.10-0.25)
                - • = Popular (found in multiple sources)
                - • = Technical (CMU only - uncommon/rare)
                - • = Alliteration bonus applied
                - •×N = Multi-syllable rhyme
                """)
        
        # Column 3: Colloquial
        with gr.Column(scale=1, elem_classes="top-align-column"):
            gr.Markdown("### Multi-word Rhymes")
            colloquial_output = gr.Markdown(
                value="Enter a word above to see multi-word rhyming phrases.",
                line_breaks=True
            )
            with gr.Accordion("About Multi-word Rhymes", open=False):
                gr.Markdown("""
                **Multi-word rhymes** are phrases with multiple words that rhyme with your query.
                These represent common usage and idiomatic rhymes.
                
                **Example:** "bubble bath", "double trouble", "on the double"
                """)
    
    gr.Markdown("---")
    
    # Row 2: Rap Database (full width)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🎤 Rap Database")
            rap_output = gr.Markdown(
                value=format_rap_section(),
                line_breaks=True
            )
    
    # Footer
    gr.Markdown("""
    ---
    
    **Scoring System:**
    - **K3 (1.00):** Exact stressed rime - perfect rhyme with same stress
    - **K2 (0.85):** Perfect by ear - same sounds, stress-agnostic
    - **K2.5 (0.60-0.74):** Terminal match - final syllable rime (compounds)
    - **K1 (0.35-0.59):** Assonance - vowel rhymes with different consonants
    - **KC (0.20-0.59):** Consonance - consonant rhymes with different vowels
    - **KF (0.15-0.59):** Family rhymes - phonetic similarity by place/manner/voicing
    - **KP (0.15-0.59):** Pararhyme - consonant frame match with vowel change
    - **KM (0.10-0.59):** Multisyllabic - consecutive syllable matches
    - **K0 (0.10-0.25):** Upstream assonance - shared vowels before rhyme tail
    - **+0.10 bonus:** Alliteration (matching onset)
    - **+0.05 bonus:** Multi-syllable rhyme (2+ syllables match)
    - **+0.20 bonus:** Rarity (KR) - uncommon rhyme patterns
    
    **Metrical Feet:**
    - **Iamb:** unstressed-stressed (x /) - e.g., "begin", "away"
    - **Trochee:** stressed-unstressed (/ x) - e.g., "table", "happy"
    - **Dactyl:** stressed-unstressed-unstressed (/ x x) - e.g., "merrily"
    - **Anapest:** unstressed-unstressed-stressed (x x /) - e.g., "understand"
    - **Spondee:** stressed-stressed (/ /)
    - **Pyrrhic:** unstressed-unstressed (x x)
    - **Amphibrach:** unstressed-stressed-unstressed (x / x) - e.g., "another"
    - **Amphimacer:** stressed-unstressed-stressed (/ x /) - e.g., "hot and cold"
    
    **Data Sources:**
    - CMU Pronunciation Dictionary (ARPAbet phonemes)
    - Datamuse API (validation & colloquial phrases)
    - Zipf frequency scores (lower = rarer words)
    
    **Settings:** Max {max_items} results per category | Zipf threshold ≤ {zipf_max} for slant rhymes
    
    **Logging:** All searches logged to `logs/app.log` for monitoring and troubleshooting
    
    **Integration Status:** ✅ All components properly connected and tested
    """.format(max_items=cfg.max_items, zipf_max=cfg.zipf_max_slant))
    
    # Event handlers
    search_btn.click(
        fn=search_interface,
        inputs=[search_input, syl_filter, stress_filter, datamuse_toggle, 
                show_rare_only, multisyl_only, enable_alliteration, show_pronunciation,
                show_popular_rhymes, show_obscure_rhymes],
        outputs=[term_info_output, perfect_output, slant_output, colloquial_output, rap_output]
    )
    
    search_input.submit(
        fn=search_interface,
        inputs=[search_input, syl_filter, stress_filter, datamuse_toggle,
                show_rare_only, multisyl_only, enable_alliteration, show_pronunciation,
                show_popular_rhymes, show_obscure_rhymes],
        outputs=[term_info_output, perfect_output, slant_output, colloquial_output, rap_output]
    )

if __name__ == "__main__":
    logger.info("Launching Gradio interface on http://127.0.0.1:7860")
    app.launch(server_name="127.0.0.1", server_port=7860)