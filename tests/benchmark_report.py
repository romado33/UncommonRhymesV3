#!/usr/bin/env python3
"""
Generate visual HTML report from benchmark results.

Shows:
- Datamuse overlap analysis
- Technical-only rhymes (our unique value)
- Missed rhymes (areas for improvement)
- Quality metrics (duplicates, zipf violations)
- Phonetic validation results
"""

import argparse
import csv
import html
import logging
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def parse_csv(csv_path: Path):
    """Load benchmark CSV results"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def generate_html_report(csv_path: Path, output_html: Path):
    """Generate comprehensive HTML report"""
    
    rows = parse_csv(csv_path)
    
    # Group by query
    by_query = defaultdict(list)
    for row in rows:
        by_query[row['query']].append(row)
    
    # Extract phonetic validation (same for all rows)
    phonetic_validation = {}
    if rows:
        phonetic_validation = {
            'dollar_family': rows[0].get('phonetic_dollar_family_ok', ''),
            'chart_family': rows[0].get('phonetic_chart_family_ok', ''),
            'no_contamination': rows[0].get('phonetic_no_contamination', '')
        }
    
    # Build HTML
    parts = []
    
    # HTML header
    parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RhymeRarity Benchmark Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
            background: #f8f9fa;
            color: #212529;
        }
        h1 {
            color: #0d6efd;
            border-bottom: 3px solid #0d6efd;
            padding-bottom: 12px;
        }
        h2 {
            color: #495057;
            margin-top: 36px;
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 8px;
        }
        h3 {
            color: #6c757d;
            margin-top: 24px;
        }
        .summary-box {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 12px 16px;
            background: #e9ecef;
            border-radius: 6px;
            font-weight: 500;
        }
        .metric.good { background: #d1e7dd; color: #0f5132; }
        .metric.warning { background: #fff3cd; color: #664d03; }
        .metric.danger { background: #f8d7da; color: #842029; }
        .query-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .query-header {
            font-size: 1.3em;
            font-weight: 600;
            color: #0d6efd;
            margin-bottom: 16px;
        }
        .bucket-results {
            margin: 12px 0;
            padding: 12px;
            background: #f8f9fa;
            border-left: 4px solid #0d6efd;
            border-radius: 4px;
        }
        .stat-line {
            margin: 6px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
        }
        .technical-only {
            color: #198754;
            font-weight: 600;
        }
        .we-missed {
            color: #dc3545;
            font-style: italic;
        }
        .recall-bar {
            display: inline-block;
            height: 20px;
            background: #0d6efd;
            border-radius: 4px;
            margin-left: 8px;
        }
        .recall-bar-container {
            display: inline-block;
            width: 200px;
            height: 20px;
            background: #e9ecef;
            border-radius: 4px;
            vertical-align: middle;
        }
        code {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .phonetic-validation {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 6px solid #198754;
        }
        .validation-item {
            margin: 8px 0;
            font-size: 1.1em;
        }
        .validation-item.pass { color: #198754; }
        .validation-item.fail { color: #dc3545; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            background: white;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background: #e9ecef;
            font-weight: 600;
            color: #495057;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .footer {
            margin-top: 48px;
            padding-top: 24px;
            border-top: 2px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
""")
    
    parts.append("<h1>🎯 RhymeRarity Comprehensive Benchmark Report</h1>")
    parts.append(f"<p style='color: #6c757d;'>Source: <code>{html.escape(str(csv_path))}</code></p>")
    
    # Summary statistics
    total_queries = len(by_query)
    total_our = sum(int(r.get('our_count', 0)) for r in rows)
    total_datamuse = sum(int(r.get('datamuse_total', 0)) for r in rows if r.get('datamuse_total'))
    total_technical = sum(int(r.get('technical_only_count', 0)) for r in rows)
    total_missed = sum(int(r.get('we_missed_count', 0)) for r in rows)
    recalls = [float(r.get('recall_pct', 0)) for r in rows if r.get('recall_pct')]
    avg_recall = sum(recalls) / len(recalls) if recalls else 0
    
    errors = sum(1 for r in rows if r.get('error'))
    has_dupes = sum(1 for r in rows if r.get('has_duplicates') == 'True')
    zipf_violations = sum(int(r.get('zipf_violations', 0)) for r in rows)
    
    parts.append("<div class='summary-box'>")
    parts.append("<h2>📊 Executive Summary</h2>")
    parts.append(f"<div class='metric'>Total Queries: <strong>{total_queries}</strong></div>")
    parts.append(f"<div class='metric'>Our Rhymes: <strong>{total_our}</strong></div>")
    parts.append(f"<div class='metric'>Datamuse Rhymes: <strong>{total_datamuse}</strong></div>")
    parts.append(f"<div class='metric good'>Technical-Only (OUR VALUE): <strong>{total_technical}</strong></div>")
    parts.append(f"<div class='metric {"good" if avg_recall >= 90 else "warning" if avg_recall >= 70 else "danger"}'>Avg Recall: <strong>{avg_recall:.1f}%</strong></div>")
    
    if total_missed > 0:
        parts.append(f"<div class='metric warning'>Missed: <strong>{total_missed}</strong></div>")
    if errors > 0:
        parts.append(f"<div class='metric danger'>Errors: <strong>{errors}</strong></div>")
    if has_dupes > 0:
        parts.append(f"<div class='metric warning'>Duplicates Found: <strong>{has_dupes}</strong></div>")
    if zipf_violations > 0:
        parts.append(f"<div class='metric warning'>Zipf Violations: <strong>{zipf_violations}</strong></div>")
    
    parts.append("</div>")
    
    # Phonetic validation
    parts.append("<div class='phonetic-validation'>")
    parts.append("<h2>🔬 Phonetic Family Validation (Dollar/ART Fix)</h2>")
    parts.append("<p>Critical test: Ensure phonetic families are properly separated.</p>")
    
    dollar_ok = phonetic_validation.get('dollar_family', '').lower() == 'true'
    chart_ok = phonetic_validation.get('chart_family', '').lower() == 'true'
    no_contam = phonetic_validation.get('no_contamination', '').lower() == 'true'
    
    parts.append(f"<div class='validation-item {"pass" if dollar_ok else "fail"}'>")
    parts.append(f"  {'✅' if dollar_ok else '❌'} <strong>Dollar family correct</strong>: dollar/collar/holler/scholar share same K1")
    parts.append("</div>")
    
    parts.append(f"<div class='validation-item {"pass" if chart_ok else "fail"}'>")
    parts.append(f"  {'✅' if chart_ok else '❌'} <strong>Chart family correct</strong>: chart/dart/heart/art share same K1")
    parts.append("</div>")
    
    parts.append(f"<div class='validation-item {"pass" if no_contam else "fail"}'>")
    parts.append(f"  {'✅' if no_contam else '❌'} <strong>No cross-contamination</strong>: dollar K1 ≠ chart K1")
    parts.append("</div>")
    
    if dollar_ok and chart_ok and no_contam:
        parts.append("<p style='color: #198754; font-weight: 600; margin-top: 16px;'>✅ All phonetic validations PASSED!</p>")
    else:
        parts.append("<p style='color: #dc3545; font-weight: 600; margin-top: 16px;'>❌ Phonetic validation FAILED - review K-key generation logic</p>")
    
    parts.append("</div>")
    
    # Query-by-query results
    parts.append("<h2>📋 Detailed Results by Query</h2>")
    
    for query in sorted(by_query.keys()):
        query_rows = by_query[query]
        
        # Aggregate stats for this query
        our_total = sum(int(r['our_count']) for r in query_rows)
        datamuse_total = int(query_rows[0].get('datamuse_total', 0))
        overlap = int(query_rows[0].get('overlap_count', 0))
        technical = int(query_rows[0].get('technical_only_count', 0))
        missed = int(query_rows[0].get('we_missed_count', 0))
        recall = float(query_rows[0].get('recall_pct', 0))
        latency = query_rows[0].get('latency_ms', '')
        error = query_rows[0].get('error', '')
        
        parts.append("<div class='query-section'>")
        parts.append(f"<div class='query-header'>Query: <code>{html.escape(query)}</code></div>")
        
        # Stats
        parts.append(f"<div class='stat-line'>📊 Our results: <strong>{our_total}</strong> rhymes across {len(query_rows)} buckets</div>")
        parts.append(f"<div class='stat-line'>📊 Datamuse: <strong>{datamuse_total}</strong> rhymes</div>")
        
        recall_bar_width = int(recall * 2) if recall <= 100 else 200
        parts.append(f"<div class='stat-line'>🎯 Overlap: <strong>{overlap}</strong> ({recall:.1f}% recall)")
        parts.append(f"  <div class='recall-bar-container'><div class='recall-bar' style='width: {recall_bar_width}px;'></div></div>")
        parts.append("</div>")
        
        if technical > 0:
            parts.append(f"<div class='stat-line technical-only'>📚 Technical-only: <strong>{technical}</strong> (OUR UNIQUE VALUE!)</div>")
            tech_examples = query_rows[0].get('technical_only_examples', '')
            if tech_examples:
                examples = [html.escape(x) for x in tech_examples.split('|') if x]
                parts.append(f"<div class='stat-line' style='margin-left: 24px;'>Examples: {', '.join(examples)}</div>")
        
        if missed > 0:
            parts.append(f"<div class='stat-line we-missed'>⚠️ We missed: <strong>{missed}</strong> rhymes</div>")
            missed_examples = query_rows[0].get('we_missed_examples', '')
            if missed_examples:
                examples = [html.escape(x) for x in missed_examples.split('|') if x]
                parts.append(f"<div class='stat-line' style='margin-left: 24px;'>Examples: {', '.join(examples)}</div>")
        
        if latency:
            parts.append(f"<div class='stat-line'>⏱️ Latency: <strong>{latency}ms</strong></div>")
        
        if error:
            parts.append(f"<div class='stat-line' style='color: #dc3545;'>❌ Error: {html.escape(error)}</div>")
        
        # Bucket breakdown
        parts.append("<h3>Buckets:</h3>")
        for row in query_rows:
            bucket = row['bucket']
            count = row['our_count']
            parts.append(f"<div class='bucket-results'>")
            parts.append(f"  <strong>{bucket.title()}</strong>: {count} results")
            parts.append(f"</div>")
        
        parts.append("</div>")
    
    # Footer
    parts.append("<div class='footer'>")
    parts.append("<p><strong>About this benchmark:</strong></p>")
    parts.append("<ul>")
    parts.append("<li><strong>Recall</strong>: Percentage of Datamuse rhymes we also found (higher = better coverage)</li>")
    parts.append("<li><strong>Technical-only</strong>: Rhymes we found that Datamuse doesn't have (proves our unique value!)</li>")
    parts.append("<li><strong>Missed</strong>: Rhymes Datamuse found but we didn't (areas for improvement)</li>")
    parts.append("<li><strong>Phonetic validation</strong>: Tests that dollar/collar (AH family) don't match chart/dart (AR family)</li>")
    parts.append("</ul>")
    parts.append(f"<p>Generated from: <code>{html.escape(str(csv_path))}</code></p>")
    parts.append("</div>")
    
    parts.append("</body></html>")
    
    # Write HTML
    output_html.parent.mkdir(parents=True, exist_ok=True)
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    
    log.info(f"✅ Generated HTML report → {output_html}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML report from benchmark CSV")
    parser.add_argument("--csv", type=Path, default=Path("results/benchmark.csv"))
    parser.add_argument("--out", type=Path, default=Path("results/benchmark_report.html"))
    
    args = parser.parse_args()
    
    if not args.csv.exists():
        log.error(f"❌ CSV file not found: {args.csv}")
        exit(1)
    
    generate_html_report(args.csv, args.out)
