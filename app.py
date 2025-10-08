from pathlib import Path
import time
import os
import csv, io
import gradio as gr
import logging
import logging.handlers
from datetime import datetime
import traceback
import sys

# ==================== LOGGING SETUP ====================
# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

simple_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Main application logger
app_logger = logging.getLogger('UncommonRhymes')
app_logger.setLevel(logging.DEBUG)

# Console handler (shows INFO and above)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(simple_formatter)
app_logger.addHandler(console_handler)

# Main log file (rotating, keeps last 10 files of 10MB each)
main_log_handler = logging.handlers.RotatingFileHandler(
    LOGS_DIR / 'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
main_log_handler.setLevel(logging.DEBUG)
main_log_handler.setFormatter(detailed_formatter)
app_logger.addHandler(main_log_handler)

# Error log file (only errors and above)
error_log_handler = logging.handlers.RotatingFileHandler(
    LOGS_DIR / 'errors.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
error_log_handler.setLevel(logging.ERROR)
error_log_handler.setFormatter(detailed_formatter)
app_logger.addHandler(error_log_handler)

# Query log file (for tracking all searches)
query_logger = logging.getLogger('UncommonRhymes.Queries')
query_logger.setLevel(logging.INFO)
query_log_handler = logging.handlers.RotatingFileHandler(
    LOGS_DIR / 'queries.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=10,
    encoding='utf-8'
)
query_log_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
query_logger.addHandler(query_log_handler)

# Performance log file
perf_logger = logging.getLogger('UncommonRhymes.Performance')
perf_logger.setLevel(logging.INFO)
perf_log_handler = logging.handlers.RotatingFileHandler(
    LOGS_DIR / 'performance.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=5,
    encoding='utf-8'
)
perf_log_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
perf_logger.addHandler(perf_log_handler)

app_logger.info("=" * 80)
app_logger.info("UncommonRhymes Application Starting")
app_logger.info(f"Logs directory: {LOGS_DIR.absolute()}")
app_logger.info("=" * 80)

# ==================== END LOGGING SETUP ====================

# --- begin gradio_client bool-schema hotfix ---
try:
    import gradio_client.utils as _gcu
    _old_get_type = _gcu.get_type
    def _get_type_safe(schema):
        if isinstance(schema, bool):
            return "object"
        return _old_get_type(schema)
    _gcu.get_type = _get_type_safe

    _old_to_py = _gcu._json_schema_to_python_type
    def _json_schema_to_python_type_safe(schema, defs=None):
        if isinstance(schema, bool):
            return "object"
        return _old_to_py(schema, defs)
    _gcu._json_schema_to_python_type = _json_schema_to_python_type_safe
    app_logger.debug("Gradio client bool-schema hotfix applied")
except Exception as e:
    app_logger.warning(f"Could not apply gradio_client hotfix: {e}")

from rhyme_core.engine import search as _engine_search, SearchConfig
from rhyme_core.providers import datamuse as dm

app_logger.info("Modules imported successfully")

# --- adapter: keep legacy signature, forward to engine ---
def search_all_categories(
    term: str,
    max_items: int = 20,
    relax_rap: bool = True,
    include_rap: bool = False,
    zipf_max: float = 4.0,
    min_each: int = 10,
    zipf_max_multi: float = 5.5,
):
    """Main search function with logging."""
    start_time = time.time()
    
    try:
        app_logger.debug(f"Search initiated: term='{term}', max_items={max_items}, zipf_max={zipf_max}")
        query_logger.info(f"SEARCH: term='{term}' | max={max_items} | zipf={zipf_max} | multi={zipf_max_multi}")
        
        cfg = SearchConfig(
            relax_rap=relax_rap,
            include_rap=include_rap,
            max_items=max_items,
            zipf_max_perfect=zipf_max,
            zipf_max_slant=zipf_max,
            zipf_max_multi=zipf_max_multi,
        )
        
        result = _engine_search(term, cfg)
        
        elapsed = (time.time() - start_time) * 1000
        result_counts = {k: len(v) for k, v in result.items() if isinstance(v, list)}
        
        perf_logger.info(f"term='{term}' | elapsed={elapsed:.1f}ms | results={result_counts}")
        app_logger.info(f"Search completed for '{term}' in {elapsed:.1f}ms: {result_counts}")
        
        return result
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        app_logger.error(f"Search failed for '{term}' after {elapsed:.1f}ms: {str(e)}")
        app_logger.error(f"Stack trace:\n{traceback.format_exc()}")
        raise

# ---------- formatting helpers ----------
def _fmt_item(r: dict) -> str:
    """Format as 'word — Nsyl | 0101 | meter' (meter may be empty for rap rows)."""
    name = r.get("word") or r.get("target_word") or "?"
    syls = r.get("syls")
    stress = r.get("stress")
    meter = r.get("meter")
    parts = []
    if syls is not None and syls != "":
        parts.append(f"{syls} syl")
    if stress:
        parts.append(str(stress))
    if meter:
        parts.append(str(meter))
    suffix = " | ".join(parts) if parts else ""
    return f"{name} — {suffix}" if suffix else name

def _rows_to_csv(rows):
    f = io.StringIO()
    w = csv.writer(f)
    w.writerow(["rhyme", "why"])
    for rhyme, why in rows:
        w.writerow([rhyme, why])
    return f.getvalue()

def _pack_rows(items):
    return [[_fmt_item(r), r.get("why","")] for r in items]

def _fmt_query_line(res_dict):
    qi = res_dict.get("query_info")
    if not qi:
        return ""
    name = qi.get("word","?")
    syls = qi.get("syls","")
    stress = qi.get("stress","")
    meter = qi.get("meter","")
    parts = []
    if syls != "":
        parts.append(f"{syls} syl")
    if stress:
        parts.append(stress)
    if meter:
        parts.append(meter)
    meta = " | ".join(parts)
    return f"**Query:** {name}" + (f" — {meta}" if meta else "")

# ---------- Benchmark helpers ----------
def _bench_load_terms():
    """Load benchmark terms from file."""
    candidates = [
        Path("benchmark.queries_used.txt"),
        Path("data/dev/benchmark.queries_used.txt"),
        Path("tests/benchmark.queries_used.txt"),
    ]
    for p in candidates:
        if p.exists():
            terms = []
            for ln in p.read_text(encoding="utf-8").splitlines():
                t = (ln or "").strip()
                if t and not t.startswith("#"):
                    terms.append(t)
            if terms:
                app_logger.info(f"Loaded {len(terms)} benchmark terms from {p}")
                return terms
    # default small set
    app_logger.info("Using default benchmark terms (no file found)")
    return ["double", "habit", "paper", "trouble", "simple"]

def _bench_run(terms, max_items, relax_rap, include_rap, zipf_max, min_each, zipf_max_multi):
    """Run benchmarks on list of terms."""
    app_logger.info(f"Starting benchmark run with {len(terms)} terms")
    results = []
    total_time = 0.0
    
    for i, term in enumerate(terms, 1):
        start = time.time()
        try:
            res = search_all_categories(
                term,
                max_items=max_items,
                relax_rap=relax_rap,
                include_rap=include_rap,
                zipf_max=zipf_max,
                min_each=min_each,
                zipf_max_multi=zipf_max_multi,
            )
            elapsed = (time.time() - start) * 1000  # ms
            total_time += elapsed
            
            results.append({
                "term": term,
                "uncommon": len(res.get("uncommon", [])),
                "slant": len(res.get("slant", [])),
                "multiword": len(res.get("multiword", [])),
                "rap_targets": len(res.get("rap_targets", [])),
                "elapsed_ms": f"{elapsed:.1f}",
            })
            app_logger.debug(f"Benchmark {i}/{len(terms)}: '{term}' completed in {elapsed:.1f}ms")
            
        except Exception as e:
            app_logger.error(f"Benchmark failed for term '{term}': {str(e)}")
            results.append({
                "term": term,
                "uncommon": "ERROR",
                "slant": "ERROR",
                "multiword": "ERROR",
                "rap_targets": "ERROR",
                "elapsed_ms": str(e)[:50],
            })
    
    avg_time = total_time / len(terms) if terms else 0
    success_count = sum(1 for r in results if r['uncommon'] != 'ERROR')
    
    summary = f"""Benchmark Results:
Total terms: {len(terms)}
Total time: {total_time:.1f}ms
Average time: {avg_time:.1f}ms per term
Success rate: {success_count}/{len(terms)} ({100*success_count/len(terms):.1f}%)
"""
    
    app_logger.info(f"Benchmark completed: {success_count}/{len(terms)} successful, avg {avg_time:.1f}ms")
    
    # Create CSV
    csv_buffer = io.StringIO()
    csv_writer = csv.DictWriter(csv_buffer, fieldnames=["term", "uncommon", "slant", "multiword", "rap_targets", "elapsed_ms"])
    csv_writer.writeheader()
    csv_writer.writerows(results)
    
    # Save to temp file
    csv_path = Path("/tmp/benchmark_results.csv")
    csv_path.write_text(csv_buffer.getvalue())
    app_logger.info(f"Benchmark results saved to {csv_path}")
    
    return results, summary, str(csv_path)

# ---------- Datamuse helpers (non-blocking, optional) ----------
def dm_suggest(prefix: str):
    p = (prefix or "").strip()
    if not p:
        return "(type above to get suggestions)"
    try:
        app_logger.debug(f"Datamuse suggest: '{p}'")
        items = dm.sug(p, max_items=10)
        words = [it.get("word","") for it in items]
        return "Suggestions: " + (", ".join(words) if words else "(none)")
    except Exception as e:
        app_logger.error(f"Datamuse suggest failed: {str(e)}")
        return "(suggestions unavailable)"

def dm_related(term: str):
    t = (term or "").strip()
    if not t:
        return "(enter a term above)"
    try:
        app_logger.debug(f"Datamuse related: '{t}'")
        ml  = [w["word"] for w in dm.means_like(t, max_items=12)]
        syn = [w["word"] for w in dm.related(t,"syn", max_items=12)]
        trg = [w["word"] for w in dm.related(t,"trg", max_items=12)]
        adj = [w["word"] for w in dm.adjectives_for(t, max_items=12)]
        def line(lbl, arr): return f"**{lbl}:** " + (", ".join(arr) if arr else "—")
        return "\n\n".join([
            line("Means-like", ml),
            line("Synonyms", syn),
            line("Triggers", trg),
            line(f'Adjectives for "{t}"', adj),
        ])
    except Exception as e:
        app_logger.error(f"Datamuse related failed: {str(e)}")
        return "(related words unavailable)"

# ---------- main analyze callbacks ----------
def go(term, max_items, relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi):
    term = (term or "").strip()
    if not term:
        empty_tbl = [["Enter a term above.", ""]]
        empty_csv = _rows_to_csv([("Enter a term above.", "")])
        return "", empty_tbl, empty_tbl, empty_tbl, empty_tbl, empty_csv, empty_csv, empty_csv, empty_csv, ""

    try:
        res = search_all_categories(
            term,
            max_items=int(max_items),
            relax_rap=bool(relax_rap),
            include_rap=bool(include_rap),
            zipf_max=float(zipf_cutoff),
            min_each=int(min_each),
            zipf_max_multi=float(zipf_cutoff_multi),
        )

        query_line = _fmt_query_line(res)

        # Tables
        uncommon_tbl = _pack_rows(res.get("uncommon", []))
        slant_tbl    = _pack_rows(res.get("slant", []))
        multi_tbl    = _pack_rows(res.get("multiword", []))
        rap_tbl      = _pack_rows(res.get("rap_targets", []))

        # CSVs
        def no_ellipsis(rows): return [r for r in rows if not str(r[0]).startswith("...")]
        unc_csv = _rows_to_csv(no_ellipsis(uncommon_tbl))
        slt_csv = _rows_to_csv(no_ellipsis(slant_tbl))
        mul_csv = _rows_to_csv(no_ellipsis(multi_tbl))
        rap_csv = _rows_to_csv(no_ellipsis(rap_tbl))

        keys = res.get("keys", {})
        focus = res.get("focus_word", "")
        debug = (f"focus='{focus}' | k1={keys.get('k1','')} k2={keys.get('k2','')} k3={keys.get('k3','')} "
                 f"| zipf≤{zipf_cutoff} (perfect/slant), multiword zipf≤{zipf_cutoff_multi}, min_each={min_each}")

        return query_line, uncommon_tbl, slant_tbl, multi_tbl, rap_tbl, unc_csv, slt_csv, mul_csv, rap_csv, debug
        
    except Exception as e:
        error_msg = f"Error processing '{term}': {str(e)}"
        app_logger.error(error_msg)
        app_logger.error(traceback.format_exc())
        
        error_tbl = [[error_msg, "Error"]]
        error_csv = _rows_to_csv([(error_msg, "Error")])
        return "", error_tbl, error_tbl, error_tbl, error_tbl, error_csv, error_csv, error_csv, error_csv, f"ERROR: {str(e)}"

def show_all(term, bucket, relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi):
    try:
        res = search_all_categories(
            (term or "").strip(),
            max_items=10_000,
            relax_rap=bool(relax_rap),
            include_rap=bool(include_rap),
            zipf_max=float(zipf_cutoff),
            min_each=int(min_each),
            zipf_max_multi=float(zipf_cutoff_multi),
        )
        return _pack_rows(res.get(bucket, []))
    except Exception as e:
        app_logger.error(f"Show all failed for bucket '{bucket}': {str(e)}")
        return [[f"Error: {str(e)}", "Error"]]

# ---------- UI ----------
with gr.Blocks() as demo:
    gr.Markdown("# UncommonRhymesV3 — functional build")
    gr.Markdown(f"*Logs are being saved to: `{LOGS_DIR.absolute()}`*")

    with gr.Row():
        term = gr.Textbox(label="Word or phrase", scale=3, value="double")
        max_items = gr.Slider(5, 100, value=20, step=1, label="Max per category")
        zipf_cutoff = gr.Slider(2.5, 7.0, value=4.0, step=0.1, label="Zipf cutoff (perfect/slant ≤)")
        zipf_cutoff_multi = gr.Slider(3.0, 7.5, value=5.5, step=0.1, label="Zipf cutoff (multiword ≤)")
        min_each = gr.Slider(1, 30, value=10, step=1, label="Min per bucket (top-up target)")

    with gr.Row():
        relax_rap = gr.Checkbox(value=True, label="Relax rap matching (use assonance if few)")
        include_rap = gr.Checkbox(value=False, label="Include rap targets")

    with gr.Row():
        sugg_btn = gr.Button("Suggest spellings/sounds (Datamuse)")
        rel_btn  = gr.Button("Related words (Datamuse)")
    sugg_md = gr.Markdown()
    rel_md  = gr.Markdown()

    btn = gr.Button("Analyze", variant="primary")

    query_md = gr.Markdown()

    with gr.Tabs():
        with gr.Tab("Benchmarks"):
            gr.Markdown("Run benchmarks on a list of query terms (reads `benchmark.queries_used.txt` if present).")
            with gr.Row():
                bm_max = gr.Slider(5, 100, value=20, step=1, label="Max per category")
                bm_zipf = gr.Slider(2.5, 7.0, value=4.0, step=0.1, label="Zipf cutoff perfect/slant ≤")
                bm_zipf_multi = gr.Slider(3.0, 7.5, value=5.5, step=0.1, label="Zipf cutoff multiword ≤")
                bm_min_each = gr.Slider(1, 40, value=10, step=1, label="Min per bucket")
            with gr.Row():
                bm_relax_rap = gr.Checkbox(value=True, label="Relax rap matching")
                bm_include_rap = gr.Checkbox(value=False, label="Include rap targets")
            bm_btn = gr.Button("Run Benchmarks", variant="primary")
            bm_table = gr.Dataframe(headers=["term","uncommon","slant","multiword","rap_targets","elapsed_ms"], interactive=False)
            bm_summary = gr.Textbox(label="Summary", lines=14, interactive=False)
            bm_file = gr.File(label="Download CSV", interactive=False)

            def _do_bench(bm_max, bm_relax_rap, bm_include_rap, bm_zipf, bm_min_each, bm_zipf_multi):
                try:
                    terms = _bench_load_terms()
                    rows, summary, out_csv = _bench_run(
                        terms, int(bm_max), bool(bm_relax_rap), bool(bm_include_rap),
                        float(bm_zipf), int(bm_min_each), float(bm_zipf_multi)
                    )
                    # Dataframe wants list of lists
                    table = [[r["term"], r["uncommon"], r["slant"], r["multiword"], r["rap_targets"], r["elapsed_ms"]] for r in rows]
                    return table, summary, out_csv
                except Exception as e:
                    app_logger.error(f"Benchmark run failed: {str(e)}")
                    app_logger.error(traceback.format_exc())
                    error_msg = f"Benchmark failed: {str(e)}"
                    return [], error_msg, None

            bm_btn.click(
                _do_bench,
                inputs=[bm_max, bm_relax_rap, bm_include_rap, bm_zipf, bm_min_each, bm_zipf_multi],
                outputs=[bm_table, bm_summary, bm_file]
            )
        with gr.Tab("Uncommon Rhymes (perfect & uncommon)"):
            uncommon = gr.Dataframe(headers=["Rhyme", "Why"], interactive=False)
            show_all_unc = gr.Button("Show full list")
            with gr.Accordion("CSV (copy/paste)", open=False):
                unc_csv_txt = gr.Textbox(lines=8, show_label=False)

        with gr.Tab("Slant Rhymes (imperfect & uncommon)"):
            slant = gr.Dataframe(headers=["Rhyme", "Why"], interactive=False)
            show_all_slt = gr.Button("Show full list")
            with gr.Accordion("CSV (copy/paste)", open=False):
                slt_csv_txt = gr.Textbox(lines=8, show_label=False)

        with gr.Tab("Multiword Rhymes (CMU combinations)"):
            multi = gr.Dataframe(headers=["Rhyme", "Why"], interactive=False)
            show_all_mul = gr.Button("Show full list")
            with gr.Accordion("CSV (copy/paste)", open=False):
                mul_csv_txt = gr.Textbox(lines=8, show_label=False)

        with gr.Tab("Rap Targets"):
            rap = gr.Dataframe(headers=["Rhyme", "Why"], interactive=False)
            show_all_rap = gr.Button("Show full list")
            with gr.Accordion("CSV (copy/paste)", open=False):
                rap_csv_txt = gr.Textbox(lines=8, show_label=False)

    debug = gr.Markdown()

    # main analyze
    btn.click(
        go,
        inputs=[term, max_items, relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi],
        outputs=[query_md, uncommon, slant, multi, rap, unc_csv_txt, slt_csv_txt, mul_csv_txt, rap_csv_txt, debug],
    )

    # show full handlers
    show_all_unc.click(
        show_all,
        inputs=[term, gr.State("uncommon"), relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi],
        outputs=uncommon,
    )
    show_all_slt.click(
        show_all,
        inputs=[term, gr.State("slant"), relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi],
        outputs=slant,
    )
    show_all_mul.click(
        show_all,
        inputs=[term, gr.State("multiword"), relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi],
        outputs=multi,
    )
    show_all_rap.click(
        show_all,
        inputs=[term, gr.State("rap_targets"), relax_rap, include_rap, zipf_cutoff, min_each, zipf_cutoff_multi],
        outputs=rap,
    )

    # Datamuse hooks
    sugg_btn.click(dm_suggest, inputs=[term], outputs=[sugg_md])
    rel_btn.click(dm_related, inputs=[term], outputs=[rel_md])

if __name__ == "__main__":
    app_logger.info("Launching Gradio interface on http://127.0.0.1:7860")
    try:
        demo.launch(
            share=False,
            server_name="127.0.0.1",
            server_port=7860,
            inbrowser=False,
            show_api=False
        )
    except Exception as e:
        app_logger.critical(f"Failed to launch Gradio app: {str(e)}")
        app_logger.critical(traceback.format_exc())
        raise
    finally:
        app_logger.info("Application shutting down")