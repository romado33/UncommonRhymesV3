"""
Debug script to check the config settings
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rhyme_core.engine import cfg

def debug_config():
    """Debug the config settings"""
    
    print("Debugging config settings")
    print("="*60)
    
    print(f"use_uncommon_filter: {cfg.use_uncommon_filter}")
    print(f"use_datamuse: {cfg.use_datamuse}")
    print(f"uncommon_config: {cfg.uncommon_config}")
    
    if cfg.uncommon_config:
        print(f"  min_perfect_rhymes: {cfg.uncommon_config.min_perfect_rhymes}")
        print(f"  min_total_results: {cfg.uncommon_config.min_total_results}")
        print(f"  min_per_category: {cfg.uncommon_config.min_per_category}")
        print(f"  popular_cutoff_percentile: {cfg.uncommon_config.popular_cutoff_percentile}")
        print(f"  display_percentile_range: {cfg.uncommon_config.display_percentile_range}")

if __name__ == "__main__":
    debug_config()




