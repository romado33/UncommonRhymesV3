#!/usr/bin/env python3
"""
Run full benchmark suite: benchmark + report + summary

Convenience script that executes:
1. benchmark.py (run tests with Datamuse validation)
2. benchmark_report.py (generate HTML report)
3. benchmark_summarize.py (generate Markdown summary)

Usage:
    python tests/run_benchmark_suite.py
    python tests/run_benchmark_suite.py --quick  # Skip HTML report generation
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status"""
    log.info("=" * 70)
    log.info(f"🚀 {description}")
    log.info("=" * 70)
    log.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        log.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        log.error(f"❌ Command not found: {cmd[0]}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Run full RhymeRarity benchmark suite"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: skip HTML report generation (faster)"
    )
    parser.add_argument(
        "--terms",
        type=Path,
        default=Path("data/test_terms.txt"),
        help="Path to test terms file"
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="Max items per bucket"
    )
    parser.add_argument(
        "--zipf-max",
        type=float,
        default=4.0,
        help="Max zipf for uncommon/slant"
    )
    
    args = parser.parse_args()
    
    log.info("")
    log.info("=" * 70)
    log.info("🎯 RhymeRarity Benchmark Suite")
    log.info("=" * 70)
    log.info(f"Test terms: {args.terms}")
    log.info(f"Max items per bucket: {args.max_items}")
    log.info(f"Zipf threshold: {args.zipf_max}")
    log.info(f"Quick mode: {args.quick}")
    log.info("")
    
    success = True
    
    # Step 1: Run benchmark
    benchmark_cmd = [
        sys.executable,
        "tests/benchmark.py",
        "--terms", str(args.terms),
        "--out", "results/benchmark.csv",
        "--max-items", str(args.max_items),
        "--zipf-max", str(args.zipf_max)
    ]
    
    if not run_command(benchmark_cmd, "Step 1: Running Benchmark"):
        success = False
        log.error("Benchmark failed. Stopping.")
        sys.exit(1)
    
    # Step 2: Generate HTML report (unless --quick)
    if not args.quick:
        report_cmd = [
            sys.executable,
            "tests/benchmark_report.py",
            "--csv", "results/benchmark.csv",
            "--out", "results/benchmark_report.html"
        ]
        
        if not run_command(report_cmd, "Step 2: Generating HTML Report"):
            success = False
            log.warning("HTML report generation failed, but continuing...")
    else:
        log.info("⏭️  Skipping HTML report generation (quick mode)")
    
    # Step 3: Generate Markdown summary
    summary_cmd = [
        sys.executable,
        "tests/benchmark_summarize.py",
        "--csv", "results/benchmark.csv",
        "--out", "results/summary.md"
    ]
    
    if not run_command(summary_cmd, "Step 3: Generating Markdown Summary"):
        success = False
        log.warning("Markdown summary generation failed, but continuing...")
    
    # Final summary
    log.info("")
    log.info("=" * 70)
    if success:
        log.info("✅ Benchmark Suite Complete!")
    else:
        log.warning("⚠️  Benchmark suite completed with warnings")
    log.info("=" * 70)
    
    log.info("")
    log.info("📂 Output Files:")
    log.info("  - results/benchmark.csv           (detailed results)")
    if not args.quick:
        log.info("  - results/benchmark_report.html   (visual report - open in browser)")
    log.info("  - results/summary.md              (executive summary)")
    log.info("  - data/datamuse_baseline.json     (cached API responses)")
    log.info("")
    
    # Quick summary from CSV
    try:
        import csv
        
        csv_path = Path("results/benchmark.csv")
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            
            if rows:
                recalls = [float(r['recall_pct']) for r in rows if r.get('recall_pct')]
                avg_recall = sum(recalls) / len(recalls) if recalls else 0
                total_technical = sum(int(r['technical_only_count']) for r in rows)
                errors = sum(1 for r in rows if r.get('error'))
                
                phonetic_pass = (
                    rows[0].get('phonetic_dollar_family_ok', '').lower() == 'true' and
                    rows[0].get('phonetic_chart_family_ok', '').lower() == 'true' and
                    rows[0].get('phonetic_no_contamination', '').lower() == 'true'
                )
                
                log.info("📊 Quick Results:")
                log.info(f"  - Average Recall: {avg_recall:.1f}% {'✅' if avg_recall >= 90 else '⚠️' if avg_recall >= 70 else '❌'}")
                log.info(f"  - Technical-Only Rhymes: {total_technical} 🎉")
                log.info(f"  - Phonetic Validation: {'✅ PASS' if phonetic_pass else '❌ FAIL'}")
                log.info(f"  - Errors: {errors} {'✅' if errors == 0 else '❌'}")
                log.info("")
                
                if avg_recall >= 90 and phonetic_pass and errors == 0:
                    log.info("🎉 All tests PASSED! Engine is working correctly.")
                elif avg_recall >= 70:
                    log.warning("⚠️  Tests passed with warnings. Review results for improvements.")
                else:
                    log.error("❌ Tests FAILED. Review results and fix issues.")
    except Exception as e:
        log.warning(f"Could not parse results: {e}")
    
    log.info("")
    log.info("👉 Next steps:")
    if not args.quick:
        log.info("  - Open results/benchmark_report.html in your browser for detailed analysis")
    log.info("  - Read results/summary.md for executive overview")
    log.info("  - Check results/benchmark.csv for raw data")
    log.info("")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
