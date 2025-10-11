#!/usr/bin/env python3
"""
NO-FILTER Benchmark - Fair comparison with Datamuse

Removes zipf filtering to match Datamuse's approach.
This shows our TRUE recall without artificial filtering.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set
from collections import defaultdict
from datetime import datetime

import requests

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Import search function
try:
    from rhyme_core.search import search_all_categories
    log.info("✅ Imported search_all_categories")
except ImportError as e:
    log.error(f"❌ Cannot import: {e}")
    sys.exit(1)

# ============================================================================
# DATAMUSE API
# ============================================================================

DATAMUSE_CACHE_FILE = Path("data/datamuse_baseline.json")
DATAMUSE_API_BASE = "https://api.datamuse.com/words"
DATAMUSE_TIMEOUT = 5

def load_datamuse_cache() -> Dict[str, Any]:
    if DATAMUSE_CACHE_FILE.exists():
        try:
            with open(DATAMUSE_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Failed to load cache: {e}")
    return {}

def save_datamuse_cache(cache: Dict[str, Any]):
    DATAMUSE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(DATAMUSE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Cache save failed: {e}")

def query_datamuse(term: str, cache: Dict[str, Any]) -> Dict[str, List[str]]:
    cache_key = term.lower().strip()
    
    if cache_key in cache:
        return cache[cache_key]
    
    log.info(f"  🌐 Querying Datamuse for '{term}'...")
    result = {'perfect': [], 'near': [], 'all': []}
    
    try:
        resp = requests.get(DATAMUSE_API_BASE, params={'rel_rhy': term, 'max': 100}, timeout=DATAMUSE_TIMEOUT)
        resp.raise_for_status()
        perfect = [item['word'].lower() for item in resp.json() if 'word' in item]
        result['perfect'] = perfect
        
        resp = requests.get(DATAMUSE_API_BASE, params={'rel_nry': term, 'max': 100}, timeout=DATAMUSE_TIMEOUT)
        resp.raise_for_status()
        near = [item['word'].lower() for item in resp.json() if 'word' in item]
        result['near'] = near
        
        result['all'] = list(set(perfect + near))
        log.info(f"    ✅ {len(perfect)} perfect, {len(near)} near")
        cache[cache_key] = result
        time.sleep(0.5)
    except Exception as e:
        log.warning(f"    ⚠️ Datamuse error: {e}")
    
    return result

# ============================================================================
# ANALYSIS
# ============================================================================

def extract_words_from_bucket(bucket: List[Dict[str, Any]]) -> Set[str]:
    return {item.get('word', '').lower().strip() for item in bucket if item.get('word')}

def analyze_results(our_results: Dict, datamuse_results: Dict, query: str) -> Dict:
    our_words = set()
    for bucket in ['uncommon', 'slant', 'multiword']:
        our_words.update(extract_words_from_bucket(our_results.get(bucket, [])))
    
    datamuse_words = set(w.lower().strip() for w in datamuse_results.get('all', []))
    overlap = our_words & datamuse_words
    we_missed = datamuse_words - our_words
    technical_only = our_words - datamuse_words
    recall = (len(overlap) / len(datamuse_words) * 100) if datamuse_words else 0.0
    
    return {
        'our_total': len(our_words),
        'datamuse_total': len(datamuse_words),
        'overlap_count': len(overlap),
        'we_missed_count': len(we_missed),
        'technical_only_count': len(technical_only),
        'recall_pct': recall,
        'we_missed_list': sorted(list(we_missed))[:10],  # Show more misses
        'technical_only_list': sorted(list(technical_only))[:10],
    }

# ============================================================================
# OUTPUT GENERATORS
# ============================================================================

def generate_html_report(results_rows: List[Dict], output_path: Path, summary_stats: Dict):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RhymeRarity NO-FILTER Benchmark</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               max-width: 1200px; margin: 40px auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .banner {{ background: #ff9800; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        table {{ width: 100%; background: white; border-collapse: collapse; margin: 20px 0; 
                 box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
        th {{ background: #3498db; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .recall-high {{ color: #27ae60; font-weight: bold; }}
        .recall-medium {{ color: #f39c12; font-weight: bold; }}
        .recall-low {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🎯 RhymeRarity NO-FILTER Benchmark</h1>
    <div class="banner">
        ⚠️ TESTING MODE: All zipf filters removed for fair comparison with Datamuse
    </div>
    
    <div class="summary">
        <h2>📊 Summary Statistics</h2>
        <div class="metric">
            <div class="metric-label">Queries</div>
            <div class="metric-value">{summary_stats['total_queries']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Avg Recall</div>
            <div class="metric-value {'success' if summary_stats['avg_recall'] >= 90 else 'warning' if summary_stats['avg_recall'] >= 70 else 'error'}">
                {summary_stats['avg_recall']:.1f}%
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Our Rhymes</div>
            <div class="metric-value">{summary_stats['total_our_rhymes']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Technical Only</div>
            <div class="metric-value success">{summary_stats['total_technical_only']}</div>
        </div>
    </div>
    
    <h2>📋 Detailed Results</h2>
    <table>
        <thead>
            <tr>
                <th>Query</th>
                <th>Bucket</th>
                <th>Our Count</th>
                <th>Datamuse</th>
                <th>Recall</th>
                <th>Missed</th>
                <th>Technical</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for row in results_rows:
        recall_class = 'recall-high' if row['recall_pct'] >= 90 else 'recall-medium' if row['recall_pct'] >= 70 else 'recall-low'
        html += f"""            <tr>
                <td><strong>{row['query']}</strong></td>
                <td>{row['bucket']}</td>
                <td>{row['our_count']}</td>
                <td>{row['datamuse_total']}</td>
                <td class="{recall_class}">{row['recall_pct']:.1f}%</td>
                <td>{row['we_missed_count']}</td>
                <td>{row['technical_only_count']}</td>
            </tr>
"""
    
    html += """        </tbody>
    </table>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    log.info(f"✅ HTML → {output_path}")

def generate_markdown_summary(results_rows: List[Dict], output_path: Path, summary_stats: Dict):
    md = f"""# RhymeRarity NO-FILTER Benchmark

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **TESTING MODE:** All zipf filters removed for fair Datamuse comparison

## 📊 Overall Performance

| Metric | Value |
|--------|-------|
| **Total Queries** | {summary_stats['total_queries']} |
| **Average Recall** | **{summary_stats['avg_recall']:.1f}%** |
| **Our Total Rhymes** | {summary_stats['total_our_rhymes']} |
| **Datamuse Total** | {summary_stats['total_datamuse']} |
| **Technical-Only** | {summary_stats['total_technical_only']} |
| **We Missed** | {summary_stats['total_datamuse'] - summary_stats['total_our_rhymes'] + summary_stats['total_technical_only']} |

## 📋 Per-Query Results

| Query | Recall | Our Count | Datamuse | Overlap | Missed | Technical |
|-------|--------|-----------|----------|---------|--------|-----------|
"""
    
    query_data = {}
    for row in results_rows:
        if row['query'] not in query_data:
            query_data[row['query']] = {
                'recall': row['recall_pct'],
                'our_count': 0,
                'datamuse': row['datamuse_total'],
                'overlap': row['overlap_count'],
                'missed': row['we_missed_count'],
                'technical': row['technical_only_count']
            }
        query_data[row['query']]['our_count'] += row['our_count']
    
    for query, data in query_data.items():
        status = '✅' if data['recall'] >= 90 else '⚠️' if data['recall'] >= 70 else '❌'
        md += f"| {query} | {status} {data['recall']:.1f}% | {data['our_count']} | {data['datamuse']} | {data['overlap']} | {data['missed']} | {data['technical']} |\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    log.info(f"✅ Markdown → {output_path}")

# ============================================================================
# MAIN BENCHMARK
# ============================================================================

def run_benchmark(test_terms_file: Path, output_dir: Path):
    log.info("=" * 70)
    log.info("🎯 RhymeRarity NO-FILTER Benchmark")
    log.info("⚠️  Testing Mode: All zipf filters DISABLED")
    log.info("=" * 70)
    
    if not test_terms_file.exists():
        log.error(f"❌ Test file not found: {test_terms_file}")
        sys.exit(1)
    
    terms = []
    with open(test_terms_file, 'r', encoding='utf-8') as f:
        for line in f:
            term = line.strip()
            if term and not term.startswith('#'):
                terms.append(term)
    
    log.info(f"📋 Loaded {len(terms)} test terms")
    
    datamuse_cache = load_datamuse_cache()
    output_dir.mkdir(parents=True, exist_ok=True)
    results_rows = []
    
    log.info("\n" + "=" * 70)
    log.info("🔍 Running Tests (NO FILTERS)")
    log.info("=" * 70)
    
    for i, term in enumerate(terms, 1):
        log.info(f"\n[{i}/{len(terms)}] Testing: '{term}'")
        
        datamuse_results = query_datamuse(term, datamuse_cache)
        
        start_time = time.perf_counter()
        try:
            # NO FILTERS! Get everything!
            our_results = search_all_categories(
                term,
                max_items=200,           # Get lots of results
                zipf_max=10.0,          # Essentially no filter (zipf never this high)
                min_each=50,            # Get plenty
                zipf_max_multi=10.0     # No filter for multiword too
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = ""
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)
            log.error(f"  ❌ Failed: {e}")
            our_results = {"uncommon": [], "slant": [], "multiword": []}
        
        analysis = analyze_results(our_results, datamuse_results, term)
        
        log.info(f"  📊 Our: {analysis['our_total']} | Datamuse: {analysis['datamuse_total']}")
        log.info(f"  🎯 Recall: {analysis['recall_pct']:.1f}%")
        log.info(f"  ✅ Overlap: {analysis['overlap_count']} | ❌ Missed: {analysis['we_missed_count']} | 📚 Technical: {analysis['technical_only_count']}")
        
        if analysis['we_missed_count'] > 0:
            log.warning(f"  Missing examples: {', '.join(analysis['we_missed_list'][:5])}")
        
        for bucket_name in ['uncommon', 'slant', 'multiword']:
            bucket = our_results.get(bucket_name, [])
            row = {
                'query': term,
                'bucket': bucket_name,
                'our_count': len(bucket),
                'datamuse_total': analysis['datamuse_total'],
                'overlap_count': analysis['overlap_count'],
                'we_missed_count': analysis['we_missed_count'],
                'technical_only_count': analysis['technical_only_count'],
                'recall_pct': analysis['recall_pct'],
                'latency_ms': f"{elapsed_ms:.1f}" if bucket_name == 'uncommon' else '',
                'error': error_msg,
                'we_missed_examples': '|'.join(analysis['we_missed_list'][:5]),
                'technical_only_examples': '|'.join(analysis['technical_only_list'][:5]),
            }
            results_rows.append(row)
    
    save_datamuse_cache(datamuse_cache)
    
    # Summary stats
    summary_stats = {
        'total_queries': len(terms),
        'total_our_rhymes': sum(r['our_count'] for r in results_rows),
        'total_datamuse': sum(r['datamuse_total'] for r in results_rows if r['datamuse_total']),
        'total_technical_only': sum(r['technical_only_count'] for r in results_rows),
        'avg_recall': sum(r['recall_pct'] for r in results_rows if r['recall_pct']) / len(results_rows) if results_rows else 0,
    }
    
    # Generate outputs
    csv_path = output_dir / "benchmark_nofilter.csv"
    html_path = output_dir / "benchmark_nofilter_report.html"
    md_path = output_dir / "summary_nofilter.md"
    
    # CSV
    fieldnames = ['query', 'bucket', 'our_count', 'datamuse_total', 'overlap_count',
                  'we_missed_count', 'technical_only_count', 'recall_pct', 'latency_ms',
                  'error', 'we_missed_examples', 'technical_only_examples']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_rows)
    log.info(f"✅ CSV → {csv_path}")
    
    generate_html_report(results_rows, html_path, summary_stats)
    generate_markdown_summary(results_rows, md_path, summary_stats)
    
    # Summary
    log.info("\n" + "=" * 70)
    log.info("📈 SUMMARY (NO FILTERS)")
    log.info("=" * 70)
    log.info(f"Queries: {summary_stats['total_queries']}")
    log.info(f"Average Recall: {summary_stats['avg_recall']:.1f}%")
    log.info(f"Our Rhymes: {summary_stats['total_our_rhymes']}")
    log.info(f"Datamuse: {summary_stats['total_datamuse']}")
    log.info(f"Technical-Only: {summary_stats['total_technical_only']}")
    
    if summary_stats['avg_recall'] >= 90:
        log.info(f"\n✅ EXCELLENT! System works perfectly without filters!")
    elif summary_stats['avg_recall'] >= 70:
        log.info(f"\n⚠️ GOOD, but room for improvement")
    else:
        log.error(f"\n❌ LOW RECALL - Need to investigate further")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RhymeRarity NO-FILTER Benchmark")
    parser.add_argument("--terms", type=Path, default=Path("data/test_terms.txt"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    
    run_benchmark(args.terms, args.out)