"""
Uncommon Rhyme Filtering System

This module implements intelligent filtering to show uncommon but usable rhymes,
avoiding both clichéd popular rhymes and overly obscure ones.
"""

import logging
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UncommonConfig:
    """Configuration for uncommon rhyme filtering"""
    # Percentile thresholds
    popular_cutoff_percentile: float = 0.25  # Remove top 25% most popular
    display_percentile_range: float = 0.20   # Show next 20% (the "sweet spot")
    
    # Minimum guarantees
    min_perfect_rhymes: int = 1000          # Show ALL perfect rhymes - no filtering
    min_total_results: int = 15              # Always show at least 15 total results
    min_per_category: int = 2                # Minimum per category (perfect/slant/multi-word)
    
    # Weighting for combined popularity score
    zipf_weight: float = 0.6                 # 60% weight for Zipf frequency
    datamuse_weight: float = 0.4             # 40% weight for Datamuse frequency
    
    # Perfect rhyme preservation
    preserve_perfect_rhymes: bool = True     # Keep perfect rhymes accessible
    perfect_rhyme_boost: float = 0.1         # Boost perfect rhymes in ranking

class UncommonFilter:
    """Filters rhymes to show uncommon but usable results"""
    
    def __init__(self, config: UncommonConfig = None):
        self.config = config or UncommonConfig()
    
    def calculate_combined_popularity_score(self, item: Dict[str, Any]) -> float:
        """
        Calculate combined popularity score from Zipf and Datamuse frequencies.
        Lower scores = more uncommon/rare.
        """
        # Get Zipf frequency (from CMU database)
        zipf_freq = item.get('zipf', 0.0)
        if zipf_freq == 0:
            # If no Zipf data, use a default based on source
            # CMU results are typically more technical/uncommon
            if item.get('source') == 'cmu' or not item.get('datamuse_verified', False):
                zipf_freq = 2.0  # CMU results are more uncommon
            else:
                zipf_freq = 3.0  # Datamuse results are more common
        
        # Get Datamuse frequency (normalized 0-1)
        datamuse_freq = item.get('freq', 0.0)
        if datamuse_freq == 0:
            datamuse_freq = 0.5  # Default middle frequency
        
        # Normalize Zipf to 0-1 scale (invert so lower = more uncommon)
        # Zipf typically ranges 0-7, where 0 = very rare, 7 = very common
        zipf_normalized = max(0, min(1, (7 - zipf_freq) / 7))
        
        # Combine scores (lower = more uncommon)
        combined_score = (
            self.config.zipf_weight * zipf_normalized +
            self.config.datamuse_weight * (1 - datamuse_freq)
        )
        
        # Boost perfect rhymes slightly (they're more valuable even if popular)
        if item.get('score', 0) >= 0.85:  # K2 or K3 rhymes
            combined_score += self.config.perfect_rhyme_boost
        
        return combined_score
    
    def apply_uncommon_filter(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply uncommon rhyme filtering to results.
        
        Returns:
            Dict with filtered results and metadata about what was hidden
        """
        logger.info("Applying uncommon rhyme filtering...")
        
        # Extract all rhyme items with their categories
        all_items = []
        category_mapping = {}
        
        # Collect perfect rhymes
        for item in results['perfect']['popular']:
            item_copy = item.copy()
            item_copy['category'] = 'perfect'
            item_copy['subcategory'] = 'popular'  # Store original subcategory
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'perfect'
        
        for item in results['perfect']['technical']:
            item_copy = item.copy()
            item_copy['category'] = 'perfect'
            item_copy['subcategory'] = 'technical'  # Store original subcategory
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'perfect'
        
        # Collect slant rhymes
        for item in results['slant']['near_perfect']['popular']:
            item_copy = item.copy()
            item_copy['category'] = 'slant'
            item_copy['subcategory'] = 'near_perfect_popular'
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'slant'
        
        for item in results['slant']['near_perfect']['technical']:
            item_copy = item.copy()
            item_copy['category'] = 'slant'
            item_copy['subcategory'] = 'near_perfect_technical'
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'slant'
        
        for item in results['slant']['assonance']['popular']:
            item_copy = item.copy()
            item_copy['category'] = 'slant'
            item_copy['subcategory'] = 'assonance_popular'
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'slant'
        
        for item in results['slant']['assonance']['technical']:
            item_copy = item.copy()
            item_copy['category'] = 'slant'
            item_copy['subcategory'] = 'assonance_technical'
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'slant'
        
        # Collect multi-word rhymes
        for item in results.get('colloquial', []):
            item_copy = item.copy()
            item_copy['category'] = 'multiword'
            item_copy['popularity_score'] = self.calculate_combined_popularity_score(item)
            all_items.append(item_copy)
            category_mapping[id(item_copy)] = 'multiword'
        
        if not all_items:
            logger.warning("No items to filter")
            return results
        
        # Sort by popularity score (ascending = most uncommon first)
        all_items.sort(key=lambda x: x['popularity_score'])
        
        logger.info(f"Total items before filtering: {len(all_items)}")
        
        # Calculate percentile cutoffs
        total_items = len(all_items)
        popular_cutoff_index = int(total_items * self.config.popular_cutoff_percentile)
        display_end_index = int(total_items * (self.config.popular_cutoff_percentile + self.config.display_percentile_range))
        
        # Ensure we don't exceed available items
        display_end_index = min(display_end_index, total_items)
        
        # Extract categories
        popular_items = all_items[:popular_cutoff_index]
        display_items = all_items[popular_cutoff_index:display_end_index]
        obscure_items = all_items[display_end_index:]
        
        logger.info(f"Popular items (hidden): {len(popular_items)}")
        logger.info(f"Display items (shown): {len(display_items)}")
        logger.info(f"Obscure items (hidden): {len(obscure_items)}")
        
        # Check minimum guarantees and adjust if needed
        display_items = self._ensure_minimum_results(
            display_items, popular_items, obscure_items, all_items
        )
        
        # Rebuild results structure
        filtered_results = self._rebuild_results_structure(display_items, results)
        
        # Store hidden items for potential access
        filtered_results['_hidden'] = {
            'popular': popular_items,
            'obscure': obscure_items,
            'total_hidden': len(popular_items) + len(obscure_items)
        }
        
        return filtered_results
    
    def _ensure_minimum_results(self, display_items: List[Dict], popular_items: List[Dict], 
                               obscure_items: List[Dict], all_items: List[Dict]) -> List[Dict]:
        """Ensure minimum result guarantees are met"""
        
        # Count by category
        display_by_category = {}
        for item in display_items:
            cat = item['category']
            display_by_category[cat] = display_by_category.get(cat, 0) + 1
        
        # Check minimum per category
        for category in ['perfect', 'slant', 'multiword']:
            current_count = display_by_category.get(category, 0)
            
            # Use specific minimum for perfect rhymes, otherwise use general minimum
            if category == 'perfect':
                min_needed = self.config.min_perfect_rhymes
            else:
                min_needed = self.config.min_per_category
            
            if current_count < min_needed:
                # Find more items of this category from hidden items
                needed = min_needed - current_count
                
                # Try popular items first, then obscure
                for source_items in [popular_items, obscure_items]:
                    category_items = [item for item in source_items if item['category'] == category]
                    if len(category_items) >= needed:
                        # Add the most uncommon ones from this source
                        category_items.sort(key=lambda x: x['popularity_score'])
                        display_items.extend(category_items[:needed])
                        # Remove from source
                        for item in category_items[:needed]:
                            source_items.remove(item)
                        break
        
        # Check total minimum
        if len(display_items) < self.config.min_total_results:
            needed = self.config.min_total_results - len(display_items)
            # Add most uncommon items from hidden sources
            all_hidden = popular_items + obscure_items
            all_hidden.sort(key=lambda x: x['popularity_score'])
            display_items.extend(all_hidden[:needed])
            # Remove from sources
            for item in all_hidden[:needed]:
                if item in popular_items:
                    popular_items.remove(item)
                elif item in obscure_items:
                    obscure_items.remove(item)
        
        return display_items
    
    def _rebuild_results_structure(self, display_items: List[Dict], original_results: Dict) -> Dict:
        """Rebuild the results structure with filtered items"""
        
        # Initialize empty structure
        filtered_results = {
            'perfect': {'popular': [], 'technical': []},
            'slant': {
                'near_perfect': {'popular': [], 'technical': []},
                'assonance': {'popular': [], 'technical': []},
                'fallback': []
            },
            'colloquial': []
        }
        
        # Categorize display items back into the structure using stored subcategory
        for item in display_items:
            category = item['category']
            subcategory = item.get('subcategory', '')
            
            if category == 'perfect':
                if subcategory == 'popular':
                    filtered_results['perfect']['popular'].append(item)
                elif subcategory == 'technical':
                    filtered_results['perfect']['technical'].append(item)
                else:
                    # Fallback to old logic if subcategory not found
                    if item.get('freq', 0) >= 2.0:
                        filtered_results['perfect']['popular'].append(item)
                    else:
                        filtered_results['perfect']['technical'].append(item)
            
            elif category == 'slant':
                if subcategory == 'near_perfect_popular':
                    filtered_results['slant']['near_perfect']['popular'].append(item)
                elif subcategory == 'near_perfect_technical':
                    filtered_results['slant']['near_perfect']['technical'].append(item)
                elif subcategory == 'assonance_popular':
                    filtered_results['slant']['assonance']['popular'].append(item)
                elif subcategory == 'assonance_technical':
                    filtered_results['slant']['assonance']['technical'].append(item)
                else:
                    # Fallback to old logic if subcategory not found
                    score = item.get('score', 0)
                    if score >= 0.60:  # Near-perfect
                        if item.get('freq', 0) >= 2.0:
                            filtered_results['slant']['near_perfect']['popular'].append(item)
                        else:
                            filtered_results['slant']['near_perfect']['technical'].append(item)
                    else:  # Assonance
                        if item.get('freq', 0) >= 2.0:
                            filtered_results['slant']['assonance']['popular'].append(item)
                        else:
                            filtered_results['slant']['assonance']['technical'].append(item)
            
            elif category == 'multiword':
                filtered_results['colloquial'].append(item)
        
        return filtered_results
    
    def get_hidden_summary(self, results: Dict) -> Dict[str, Any]:
        """Get summary of hidden rhymes for UI display"""
        hidden = results.get('_hidden', {})
        
        return {
            'popular_count': len(hidden.get('popular', [])),
            'obscure_count': len(hidden.get('obscure', [])),
            'total_hidden': hidden.get('total_hidden', 0),
            'has_popular': len(hidden.get('popular', [])) > 0,
            'has_obscure': len(hidden.get('obscure', [])) > 0
        }
