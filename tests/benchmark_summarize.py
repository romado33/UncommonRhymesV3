#!/usr/bin/env python3
"""
Generate concise Markdown summary from benchmark results.

Quick executive overview showing:
- Overall pass/fail status
- Key metrics
- Top technical-only wins
- Critical issues
"""

import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def parse_csv(csv_path: Path):
    """Load benchmark CSV results"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def generate_summary(csv_path: Path, output_md: Path):
    """Generate executive summary in Markdown"""
    
    rows = parse_csv(csv_path)
    
    if not rows:
        log.error("No data in CSV file")
        return
    
    # Group by query
    by_query = defaultdict(list)
    for row in rows:
        by_query[row['query']].append(row)
    
    # Calculate overall stats
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
    
    # Phonetic validation
    phonetic = {
        'dollar_ok': rows[0].get('phonetic_dollar_family_ok', '').lower() == 'true',
        'chart_ok': rows[0].get('phonetic_chart_family_ok', '').lower() == 'true',
        'no_contam': rows[0].get('phonetic_no_contamination', '').lower() == 'true',
    }
    phonetic_pass = all(phonetic.values())
    
    # Find top technical-only wins
    technical_by_query = {}
    for query, query_rows in by_query.items():
        count = int(query_rows[0].get('technical_only_count', 0))
        examples = query_rows[0].get('technical_only_examples', '')
        if count > 0:
            technical_by_query[query] = (count, examples)
    
    top_technical = sorted(technical_by_query.items(), key=lambda x: x[1][0], reverse=True)[:5]
    
    # Find queries with most missed rhymes
    missed_by_query = {}
    for query, query_rows in by_query.items():
        count = int(query_rows[0].get('we_missed_count', 0))
        examples = query_rows[0].get('we_missed_examples', '')
        if count > 0:
            missed_by_query[query] = (count, examples)
    
    top_missed = sorted(missed_by_query.items(), key=lambda x: x[1][0], reverse=True)[:5]
    
    # Build markdown
    lines = []
    
    lines.append("# 🎯 RhymeRarity Benchmark Summary")
    lines.append("")
    lines.append(f"**Source**: `{csv_path}`")
    lines.append("")
    
    # Overall status
    lines.append("## 📊 Overall Status")
    lines.append("")
    
    # Determine pass/fail
    overall_pass = (
        avg_recall >= 80.0 and
        phonetic_pass and
        errors == 0 and
        has_dupes == 0
    )
    
    status_emoji = "✅" if overall_pass else "⚠️" if avg_recall >= 70 else "❌"
    status_text = "PASS" if overall_pass else "WARNING" if avg_recall >= 70 else "FAIL"
    
    lines.append(f"### {status_emoji} Benchmark Status: **{status_text}**")
    lines.append("")
    
    # Key metrics
    lines.append("## 📈 Key Metrics")
    lines.append("")
    lines.append(f"- **Total Queries**: {total_queries}")
    lines.append(f"- **Our Rhymes Found**: {total_our}")
    lines.append(f"- **Datamuse Rhymes**: {total_datamuse}")
    lines.append(f"- **Average Recall**: {avg_recall:.1f}% {'✅' if avg_recall >= 90 else '⚠️' if avg_recall >= 70 else '❌'}")
    lines.append(f"- **Technical-Only Rhymes** (OUR VALUE): **{total_technical}** 🎉")
    
    if total_missed > 0:
        lines.append(f"- **Missed Rhymes**: {total_missed} ⚠️")
    if errors > 0:
        lines.append(f"- **Errors**: {errors} ❌")
    if has_dupes > 0:
        lines.append(f"- **Duplicates Found**: {has_dupes} ⚠️")
    if zipf_violations > 0:
        lines.append(f"- **Zipf Violations**: {zipf_violations} ⚠️")
    
    lines.append("")
    
    # Phonetic validation
    lines.append("## 🔬 Phonetic Validation (Dollar/ART Fix)")
    lines.append("")
    
    lines.append(f"- **Dollar family correct**: {'✅ PASS' if phonetic['dollar_ok'] else '❌ FAIL'}")
    lines.append(f"- **Chart family correct**: {'✅ PASS' if phonetic['chart_ok'] else '❌ FAIL'}")
    lines.append(f"- **No cross-contamination**: {'✅ PASS' if phonetic['no_contam'] else '❌ FAIL'}")
    lines.append("")
    
    if phonetic_pass:
        lines.append("**Result**: ✅ All phonetic validations PASSED! K1/K2/K3 extraction is working correctly.")
    else:
        lines.append("**Result**: ❌ Phonetic validation FAILED! Review K-key generation logic in phonetics.py")
    
    lines.append("")
    
    # Top technical wins
    if top_technical:
        lines.append("## 🏆 Top Technical-Only Wins (Our Unique Value)")
        lines.append("")
        lines.append("These are rhymes we found that Datamuse doesn't have - our competitive advantage!")
        lines.append("")
        
        for query, (count, examples) in top_technical:
            example_list = [x.strip() for x in examples.split('|') if x.strip()]
            examples_str = ', '.join(f'`{e}`' for e in example_list[:5])
            lines.append(f"- **`{query}`**: {count} technical rhymes — {examples_str}")
        
        lines.append("")
    
    # Missed rhymes
    if top_missed:
        lines.append("## ⚠️ Top Gaps (Rhymes We Missed)")
        lines.append("")
        lines.append("These are rhymes Datamuse found but we didn't - areas for improvement.")
        lines.append("")
        
        for query, (count, examples) in top_missed:
            example_list = [x.strip() for x in examples.split('|') if x.strip()]
            examples_str = ', '.join(f'`{e}`' for e in example_list[:3])
            lines.append(f"- **`{query}`**: {count} missed — {examples_str}")
        
        lines.append("")
    
    # Query-by-query breakdown
    lines.append("## 📋 Query-by-Query Breakdown")
    lines.append("")
    
    for query in sorted(by_query.keys()):
        query_rows = by_query[query]
        our_total = sum(int(r['our_count']) for r in query_rows)
        datamuse_total = int(query_rows[0].get('datamuse_total', 0))
        recall = float(query_rows[0].get('recall_pct', 0))
        technical = int(query_rows[0].get('technical_only_count', 0))
        missed = int(query_rows[0].get('we_missed_count', 0))
        error = query_rows[0].get('error', '')
        
        status = "✅" if recall >= 90 and not error else "⚠️" if recall >= 70 else "❌"
        
        lines.append(f"### {status} `{query}`")
        lines.append("")
        lines.append(f"- **Our results**: {our_total} rhymes")
        lines.append(f"- **Datamuse**: {datamuse_total} rhymes")
        lines.append(f"- **Recall**: {recall:.1f}%")
        
        if technical > 0:
            lines.append(f"- **Technical-only**: {technical} 🎉")
        if missed > 0:
            lines.append(f"- **Missed**: {missed} ⚠️")
        if error:
            lines.append(f"- **Error**: {error} ❌")
        
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## 📖 Understanding the Metrics")
    lines.append("")
    lines.append("- **Recall**: % of Datamuse rhymes we also found (target: 90%+)")
    lines.append("- **Technical-only**: Rhymes only we have from CMU Dictionary (proves unique value)")
    lines.append("- **Missed**: Rhymes Datamuse found but we didn't (investigate for improvements)")
    lines.append("- **Phonetic validation**: Tests that phonetic families don't leak (dollar ≠ chart)")
    lines.append("")
    lines.append("**Artifacts**: `benchmark.csv`, `benchmark_report.html`, `test_terms.txt`")
    lines.append("")
    
    # Write markdown
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    log.info(f"✅ Generated summary → {output_md}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Markdown summary from benchmark CSV")
    parser.add_argument("--csv", type=Path, default=Path("results/benchmark.csv"))
    parser.add_argument("--out", type=Path, default=Path("results/summary.md"))
    
    args = parser.parse_args()
    
    if not args.csv.exists():
        log.error(f"❌ CSV file not found: {args.csv}")
        exit(1)
    
    generate_summary(args.csv, args.out)
