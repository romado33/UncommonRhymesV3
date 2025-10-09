#!/usr/bin/env python3
"""
Anti-LLM Rhyme Engine - Enhanced Gradio UI with Competitor Features
Visual improvements: popularity bars, syllable grouping, pronunciation display
WITH COMPREHENSIVE LOGGING for troubleshooting and monitoring
"""

import gradio as gr
from rhyme_core.engine import search_rhymes, get_result_counts, organize_by_syllables, cfg
import logging
from pathlib import Path
from datetime import datetime
import uuid
import time

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
# FORMATTING FUNCTIONS
# =============================================================================

def format_popularity_bar(zipf: float) -> str:
    """
    Create visual popularity bar from zipf score.
    Zipf 0-2 = rare (1-2 bars)
    Zipf 2-4 = uncommon (3-5 bars)
    Zipf 4-6 = common (6-8 bars)
    Zipf 6+ = very common (9-10 bars)
    """
    bars_filled = min(10, max(1, int((zipf / 7.0) * 10)))
    filled = "█" * bars_filled
    empty = "░" * (10 - bars_filled)
    return f"{filled}{empty}"

def format_rhyme_item(item: dict, emoji: str = "", show_pronunciation: bool = False) -> str:
    """Format a single rhyme result with emoji, visual popularity, and optional pronunciation"""
    word = item['word']
    score = item['score']
    zipf = item['zipf']
    syls = item['syls']
    stress = item['stress']
    pron = item.get('pron', '')
    has_alliteration = item.get('has_alliteration', False)
    matching_syls = item.get('matching_syllables', 0)
    
    # Visual popularity bar
    pop_bar = format_popularity_bar(zipf)
    
    # Format stress pattern nicely
    stress_display = stress.replace('-', '‑')  # Non-breaking hyphen
    
    # Build display string
    result = f"{emoji} **{word}** ({pop_bar})"
    
    # Add alliteration indicator
    if has_alliteration:
        result += " 🔤"
    
    # Add multi-syllable indicator
    if matching_syls >= 2:
        result += f" 🎵×{matching_syls}"
    
    result += f" ({syls}syl, {stress_display})"
    
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
        for item in syl_items:
            output.append(format_rhyme_item(item, emoji, show_pronunciation))
        
    return output

def format_perfect_tab(results: dict, counts: dict, show_pronunciation: bool = False) -> str:
    """Format Perfect Rhymes tab with Popular/Technical subsections organized by syllables"""
    output = []
    
    perfect_pop = results['perfect']['popular']
    perfect_tech = results['perfect']['technical']
    
    if not perfect_pop and not perfect_tech:
        return "No perfect rhymes found. Try the Slant Rhymes tab for approximate matches."
    
    # Popular section (both sources)
    if perfect_pop:
        output.append("### ✓✓ Popular Perfect Rhymes")
        output.append("*Found in both CMU Dictionary and Datamuse - widely recognized*\n")
        
        # Organize by syllables
        by_syl = organize_by_syllables(perfect_pop)
        for syl_count in sorted(by_syl.keys()):
            syl_items = by_syl[syl_count]
            output.append(f"\n**{syl_count}-syllable ({len(syl_items)} rhymes):**\n")
            for item in syl_items:
                emoji = "⭐" if item['score'] >= 1.00 else "✓"
                output.append(format_rhyme_item(item, emoji, show_pronunciation))
        
        output.append("")  # Blank line
    
    # Technical section (CMU only) - OUR SPECIALTY
    if perfect_tech:
        output.append("### 📚 Technical Perfect Rhymes")
        output.append("*Found only in CMU Dictionary - rare/archaic/technical terms*")
        output.append("*This is our unique value proposition!*\n")
        
        # Organize by syllables
        by_syl = organize_by_syllables(perfect_tech)
        for syl_count in sorted(by_syl.keys()):
            syl_items = by_syl[syl_count]
            output.append(f"\n**{syl_count}-syllable ({len(syl_items)} rhymes):**\n")
            for item in syl_items:
                emoji = "⭐" if item['score'] >= 1.00 else "✓"
                output.append(format_rhyme_item(item, emoji, show_pronunciation))
        
        output.append("")
    
    # Summary stats
    total = counts['perfect_popular'] + counts['perfect_technical']
    output.append(f"\n---")
    output.append(f"**Total:** {total} perfect rhymes ({counts['perfect_popular']} popular, {counts['perfect_technical']} technical)")
    
    return "\n".join(output)

def format_slant_tab(results: dict, counts: dict, show_pronunciation: bool = False) -> str:
    """Format Slant Rhymes tab with visual grouping and Popular/Technical subsections"""
    output = []
    
    near_pop = results['slant']['near_perfect']['popular']
    near_tech = results['slant']['near_perfect']['technical']
    asso_pop = results['slant']['assonance']['popular']
    asso_tech = results['slant']['assonance']['technical']
    fallback = results['slant']['fallback']
    
    if not any([near_pop, near_tech, asso_pop, asso_tech, fallback]):
        return "No slant rhymes found. Try adjusting filters or check other tabs."
    
    # NEAR-PERFECT SECTION (0.60-0.74)
    if near_pop or near_tech:
        output.append("## 🎯 NEAR-PERFECT SLANT RHYMES")
        output.append("*Very close to perfect - strong imperfect rhymes (score 0.60-0.74)*\n")
        
        if near_pop:
            output.append("### ✓✓ Popular Near-Perfect")
            output.append("*Recognized by multiple sources*\n")
            output.extend(format_syllable_section(near_pop, "🎯", show_pronunciation))
            output.append("")
        
        if near_tech:
            output.append("### 📚 Technical Near-Perfect")
            output.append("*Uncommon finds - only in CMU Dictionary*\n")
            output.extend(format_syllable_section(near_tech, "🎯", show_pronunciation))
            output.append("")
    
    # ASSONANCE SECTION (0.35-0.59)
    if asso_pop or asso_tech:
        output.append("## ≈ ASSONANCE (Vowel Rhymes)")
        output.append("*Same vowel sound, different consonants (score 0.35-0.59)*\n")
        
        if asso_pop:
            output.append("### ✓✓ Popular Assonance")
            output.append("*Recognized by multiple sources*\n")
            output.extend(format_syllable_section(asso_pop, "≈", show_pronunciation))
            output.append("")
        
        if asso_tech:
            output.append("### 📚 Technical Assonance")
            output.append("*Uncommon finds - only in CMU Dictionary*\n")
            output.extend(format_syllable_section(asso_tech, "≈", show_pronunciation))
            output.append("")
    
    # FALLBACK SECTION (only if total slant < 5)
    if fallback and counts['total_slant'] < 5:
        output.append("## ⚠️ FALLBACK MATCHES")
        output.append("*Weak matches shown due to limited results (score < 0.35)*\n")
        for item in fallback:
            output.append(format_rhyme_item(item, "⚠️", show_pronunciation))
        output.append("")
    
    # Summary stats
    total_slant = counts['total_slant']
    total_with_fallback = total_slant + (counts['fallback'] if counts['total_slant'] < 5 else 0)
    output.append(f"\n---")
    output.append(f"**Total:** {total_with_fallback} slant rhymes")
    output.append(f"- Near-Perfect: {counts['near_perfect_popular'] + counts['near_perfect_technical']} ({counts['near_perfect_popular']} popular, {counts['near_perfect_technical']} technical)")
    output.append(f"- Assonance: {counts['assonance_popular'] + counts['assonance_technical']} ({counts['assonance_popular']} popular, {counts['assonance_technical']} technical)")
    if fallback and counts['total_slant'] < 5:
        output.append(f"- Fallback: {counts['fallback']}")
    
    return "\n".join(output)

def format_colloquial_tab(results: dict, counts: dict) -> str:
    """Format Colloquial tab (Datamuse multi-word phrases)"""
    output = []
    
    colloquial = results['colloquial']
    
    if not colloquial:
        return "No colloquial phrases found. These are multi-word rhyming expressions from Datamuse."
    
    output.append("## 💬 Colloquial Rhyming Phrases")
    output.append("*Multi-word expressions and phrases that rhyme*")
    output.append("*Source: Datamuse API (common usage)*\n")
    
    for item in colloquial:
        output.append(f"💬 **{item['word']}**")
    
    output.append(f"\n---")
    output.append(f"**Total:** {counts['colloquial']} colloquial phrases")
    
    return "\n".join(output)

def format_rap_tab() -> str:
    """Format Rap Database tab (placeholder)"""
    return """## 🎤 Rap Rhyme Database

*Coming soon: Culturally-informed rhymes from hip-hop lyrics and poetry*

This tab will feature:
- Multi-syllable rhymes from rap lyrics
- Slant rhymes popular in hip-hop culture
- Regional pronunciation variants
- Battle rap schemes and patterns

Stay tuned!"""

# =============================================================================
# SEARCH INTERFACE WITH LOGGING
# =============================================================================

def search_interface(term: str, syl_filter: str, stress_filter: str, 
                     use_datamuse: bool, show_rare_only: bool, 
                     multisyl_only: bool, enable_alliteration: bool,
                     show_pronunciation: bool):
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
        empty_msg = "Enter a word to search for rhymes."
        logger.info(f"ui.render id={request_id} empty_term=True")
        return empty_msg, empty_msg, empty_msg, empty_msg
    
    # Start timing
    start_time = time.time()
    
    try:
        # Perform search
        results = search_rhymes(
            term.strip(), 
            syl_filter, 
            stress_filter, 
            use_datamuse,
            multisyl_only,
            enable_alliteration
        )
        
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
            'colloquial_top': [r['word'] for r in results['colloquial'][:3]]
        }
        
        # Log the results
        logger.info(
            f"ui.render id={request_id} elapsed_ms={elapsed_ms:.1f} counts={counts} preview={preview}"
        )
        
        # Format each tab
        perfect_output = format_perfect_tab(results, counts, show_pronunciation)
        slant_output = format_slant_tab(results, counts, show_pronunciation)
        colloquial_output = format_colloquial_tab(results, counts)
        rap_output = format_rap_tab()
        
        return perfect_output, slant_output, colloquial_output, rap_output
        
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"ui.error id={request_id} elapsed_ms={elapsed_ms:.1f} error={str(e)}", exc_info=True)
        error_msg = f"Error during search: {str(e)}\n\nCheck logs/app.log for details."
        return error_msg, error_msg, error_msg, error_msg

# =============================================================================
# GRADIO INTERFACE
# =============================================================================

# Build Gradio interface
with gr.Blocks(title="Anti-LLM Rhyme Engine - Enhanced", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🎯 Anti-LLM Rhyme Engine - Enhanced Edition
    
    **Find uncommon rhymes that LLMs miss and traditional dictionaries don't know.**
    
    Our unique value: **Technical rhymes (📚)** are found ONLY in the CMU Pronunciation Dictionary - nobody else has them!
    
    **New Features:** Visual popularity bars, syllable grouping, multi-syllable detection, alliteration bonuses
    
    ---
    """)
    
    # Input section
    with gr.Row():
        with gr.Column(scale=3):
            search_input = gr.Textbox(
                label="Search Term",
                placeholder="Enter a word (e.g., 'double', 'orange', 'month')",
                show_label=True
            )
        with gr.Column(scale=1):
            search_btn = gr.Button("🔍 Search", variant="primary", size="lg")
    
    # Filters section
    gr.Markdown("### 🎛️ Filters & Options")
    
    with gr.Row():
        syl_filter = gr.Dropdown(
            choices=["Any", "1", "2", "3", "4", "5+"],
            value="Any",
            label="Syllables",
            scale=1
        )
        stress_filter = gr.Dropdown(
            choices=["Any", "1-0", "0-1", "1-0-0", "0-0-1", "0-1-0"],
            value="Any",
            label="Stress Pattern",
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
    
    gr.Markdown("---")
    
    # Results tabs
    with gr.Tabs() as tabs:
        with gr.Tab("⭐ Perfect Rhymes"):
            perfect_output = gr.Markdown(
                value="Enter a word above to see perfect rhymes.",
                line_breaks=True
            )
            gr.Markdown("""
            **Legend:**
            - ⭐ = K3 strict perfect (exact stressed rime, score 1.00)
            - ✓ = K2 perfect by ear (stress-agnostic, score 0.85)
            - ✓✓ = Popular (found in both CMU and Datamuse)
            - 📚 = Technical (CMU only - our specialty!)
            - 🔤 = Alliteration (matching onset consonants)
            - 🎵×N = Multi-syllable rhyme (N syllables match)
            - ██████░░░░ = Popularity bar (more bars = more common)
            """)
        
        with gr.Tab("≈ Slant Rhymes"):
            slant_output = gr.Markdown(
                value="Enter a word above to see slant rhymes.",
                line_breaks=True
            )
            gr.Markdown("""
            **Legend:**
            - 🎯 = Near-perfect slant (score 0.60-0.74)
            - ≈ = Assonance / vowel rhyme (score 0.35-0.59)
            - ⚠️ = Fallback (weak match, shown only if few results)
            - ✓✓ = Popular (found in multiple sources)
            - 📚 = Technical (CMU only - uncommon/rare)
            - 🔤 = Alliteration bonus applied
            - 🎵×N = Multi-syllable rhyme
            """)
        
        with gr.Tab("💬 Colloquial"):
            colloquial_output = gr.Markdown(
                value="Enter a word above to see colloquial rhyming phrases.",
                line_breaks=True
            )
            gr.Markdown("""
            **Colloquial phrases** are multi-word expressions from Datamuse API.
            These represent common usage and idiomatic rhymes.
            
            Example: "bubble bath", "double trouble", "on the double"
            """)
        
        with gr.Tab("🎤 Rap Database"):
            rap_output = gr.Markdown(
                value=format_rap_tab(),
                line_breaks=True
            )
    
    # Footer
    gr.Markdown("""
    ---
    
    ### About This Enhanced Tool
    
    **Our Competitive Advantage:** We find **technical rhymes (📚)** that only exist in the CMU Pronunciation Dictionary.
    These are uncommon, archaic, or specialized terms that:
    - Traditional rhyme dictionaries don't include
    - Datamuse API doesn't return
    - LLMs hallucinate or miss entirely
    - Give users vocabulary nobody else has
    
    **Enhanced Features (Inspired by RhymeZone, B-Rhymes, Rhymer):**
    - 📊 **Visual Popularity Bars** - See word frequency at a glance
    - 📁 **Syllable Grouping** - Results organized by syllable count
    - 🔬 **Rare Only Filter** - Focus on technical rhymes
    - 🎵 **Multi-Syllable Detection** - Find double/triple rhymes
    - 🔤 **Alliteration Bonus** - Rewards matching onset consonants
    - 🗣️ **Pronunciation Display** - Educational ARPAbet phonemes
    
    **Categories Explained:**
    - **✓✓ Popular:** Found in both CMU Dictionary and Datamuse - widely recognized, high-confidence rhymes
    - **📚 Technical:** Found ONLY in CMU Dictionary - rare finds that showcase our unique database
    - **💬 Colloquial:** Multi-word phrases from Datamuse - common expressions and idioms
    
    **Scoring System:**
    - **K3 (1.00):** Exact stressed rime - perfect rhyme with same stress
    - **K2 (0.85):** Perfect by ear - same sounds, stress-agnostic
    - **Near-Perfect (0.60-0.74):** Very close slant rhymes
    - **Assonance (0.35-0.59):** Vowel rhymes with different consonants
    - **+0.10 bonus:** Alliteration (matching onset)
    - **+0.05 bonus:** Multi-syllable rhyme (2+ syllables match)
    
    **Data Sources:**
    - CMU Pronunciation Dictionary (ARPAbet phonemes)
    - Datamuse API (validation & colloquial phrases)
    - Zipf frequency scores (lower = rarer words)
    
    **Settings:** Max {max_items} results per category | Zipf threshold ≤ {zipf_max} for slant rhymes
    
    **Logging:** All searches logged to `logs/app.log` for monitoring and troubleshooting
    """.format(max_items=cfg.max_items, zipf_max=cfg.zipf_max_slant))
    
    # Event handlers
    search_btn.click(
        fn=search_interface,
        inputs=[search_input, syl_filter, stress_filter, datamuse_toggle, 
                show_rare_only, multisyl_only, enable_alliteration, show_pronunciation],
        outputs=[perfect_output, slant_output, colloquial_output, rap_output]
    )
    
    search_input.submit(
        fn=search_interface,
        inputs=[search_input, syl_filter, stress_filter, datamuse_toggle,
                show_rare_only, multisyl_only, enable_alliteration, show_pronunciation],
        outputs=[perfect_output, slant_output, colloquial_output, rap_output]
    )

if __name__ == "__main__":
    logger.info("Launching Gradio interface on http://127.0.0.1:7860")
    app.launch(server_name="127.0.0.1", server_port=7860)