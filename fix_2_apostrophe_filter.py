"""
FIX #2: FILTER APOSTROPHE WORDS FROM SEARCH RESULTS
====================================================

Problem: Database contains contractions with leading apostrophes:
- 'bout, 'cause, 'course, 'em, 'til, etc.

These are being returned as rhyme results, creating garbage output like:
- a. 'm
- are 'm  
- i. 'm
- be 'm

Root Cause: The CMU Pronouncing Dictionary includes these informal contractions
with apostrophes at the START. When queries sort alphabetically, these appear first.

Solution: Add WHERE clause filter to exclude words starting with apostrophes.

This patch provides multiple implementation options for different search architectures.
"""

# ============================================================================
# OPTION A: If you have a centralized _query_words() function
# ============================================================================

def _query_words_FIXED(where_clause, params, db_path, limit=None):
    """
    FIXED version with apostrophe filtering.
    
    Args:
        where_clause: Original WHERE conditions (e.g., "k1 = ?")
        params: Query parameters (e.g., ("AA1",))
        db_path: Path to database
        limit: Optional result limit
        
    Returns:
        List of matching words (excluding apostrophe words)
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ADD APOSTROPHE FILTER TO WHERE CLAUSE
    # Filter out words starting with apostrophe
    enhanced_where = f"({where_clause}) AND word NOT LIKE \"'%\""
    
    # Build query
    query = f"SELECT * FROM words WHERE {enhanced_where}"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return results


# ============================================================================
# OPTION B: Patch for search.py with multiple query functions
# ============================================================================

class SearchEnginePatch:
    """
    Drop-in replacement functions for search.py
    """
    
    @staticmethod
    def _select_uncommon_FIXED(k3, db_path, min_zipf=None, max_zipf=None, limit=100):
        """
        FIXED uncommon search with apostrophe filtering
        """
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build WHERE clause with apostrophe filter
        where_parts = ["k3 = ?", "word NOT LIKE \"'%\""]
        params = [k3]
        
        if min_zipf is not None:
            where_parts.append("zipf >= ?")
            params.append(min_zipf)
        
        if max_zipf is not None:
            where_parts.append("zipf <= ?")
            params.append(max_zipf)
        
        where_clause = " AND ".join(where_parts)
        
        query = f"""
            SELECT word, pron, k1, k2, k3, zipf, syls, stress 
            FROM words 
            WHERE {where_clause}
            ORDER BY zipf ASC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    @staticmethod
    def _select_slant_FIXED(k1, db_path, exclude_k3_list=None, limit=100):
        """
        FIXED slant search with apostrophe filtering
        """
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Build WHERE clause with apostrophe filter
        where_parts = ["k1 = ?", "word NOT LIKE \"'%\""]
        params = [k1]
        
        if exclude_k3_list:
            placeholders = ",".join("?" * len(exclude_k3_list))
            where_parts.append(f"k3 NOT IN ({placeholders})")
            params.extend(exclude_k3_list)
        
        where_clause = " AND ".join(where_parts)
        
        query = f"""
            SELECT word, pron, k1, k2, k3, zipf, syls, stress 
            FROM words 
            WHERE {where_clause}
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    @staticmethod
    def _select_multiword_FIXED(k2, db_path, limit=50):
        """
        FIXED multiword search with apostrophe filtering
        """
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Apostrophe filter + multiword filter (contains space)
        query = """
            SELECT word, pron, k1, k2, k3, zipf, syls, stress 
            FROM words 
            WHERE k2 = ? 
              AND word LIKE '% %'
              AND word NOT LIKE \"'%\"
            LIMIT ?
        """
        
        cursor.execute(query, (k2, limit))
        results = cursor.fetchall()
        conn.close()
        
        return results


# ============================================================================
# OPTION C: Global filter function (most flexible)
# ============================================================================

def filter_apostrophe_words(word_list):
    """
    Post-query filter to remove apostrophe words.
    
    Use this if you can't modify the database queries directly.
    
    Args:
        word_list: List of words or result tuples
        
    Returns:
        Filtered list with apostrophe words removed
    """
    
    def should_keep(item):
        # Handle different data structures
        if isinstance(item, str):
            word = item
        elif isinstance(item, (tuple, list)) and len(item) > 0:
            word = item[0]  # Assume word is first element
        elif isinstance(item, dict) and 'word' in item:
            word = item['word']
        else:
            return True  # Keep if we can't determine
        
        # Filter out apostrophe words
        return not word.startswith("'")
    
    return [item for item in word_list if should_keep(item)]


# ============================================================================
# OPTION D: Database-level fix (permanent solution)
# ============================================================================

def clean_database_apostrophe_words(db_path, dry_run=True):
    """
    Remove apostrophe words from database permanently.
    
    WARNING: This modifies the database! Use dry_run=True first.
    
    Args:
        db_path: Path to words_index.sqlite
        dry_run: If True, only show what would be deleted
        
    Returns:
        dict: Statistics about words removed
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find apostrophe words
    cursor.execute("""
        SELECT word, pron FROM words 
        WHERE word LIKE \"'%\"
        ORDER BY word
    """)
    
    apostrophe_words = cursor.fetchall()
    
    stats = {
        'found': len(apostrophe_words),
        'sample': apostrophe_words[:20],  # First 20 examples
        'deleted': 0
    }
    
    if dry_run:
        print(f"🔍 DRY RUN: Found {stats['found']} apostrophe words")
        print("\nFirst 20 examples:")
        for word, pron in stats['sample']:
            print(f"  '{word}' → {pron}")
        print(f"\n⚠️  To actually delete these, run with dry_run=False")
    else:
        # Actually delete them
        cursor.execute("""
            DELETE FROM words 
            WHERE word LIKE \"'%\"
        """)
        
        stats['deleted'] = cursor.rowcount
        conn.commit()
        
        print(f"✅ Deleted {stats['deleted']} apostrophe words from database")
    
    conn.close()
    
    return stats


# ============================================================================
# OPTION E: Quick patch for existing search.py
# ============================================================================

APOSTROPHE_FILTER_SQL = """AND word NOT LIKE \"'%\" """

"""
To quickly patch your existing search.py, add this filter to all WHERE clauses:

BEFORE:
-------
query = "SELECT * FROM words WHERE k1 = ?"

AFTER:
------
query = "SELECT * FROM words WHERE k1 = ? AND word NOT LIKE \"'%\" "

Or define it once and reuse:
----------------------------
FILTER = "AND word NOT LIKE \"'%\" "

query = f"SELECT * FROM words WHERE k1 = ? {FILTER}"
"""


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

def example_integration_centralized():
    """
    Example: If you have a centralized query function
    """
    
    # OLD CODE:
    def old_query_words(where, params, db):
        query = f"SELECT * FROM words WHERE {where}"
        # execute...
        pass
    
    # NEW CODE:
    def new_query_words(where, params, db):
        # Add apostrophe filter to every query
        enhanced_where = f"({where}) AND word NOT LIKE \"'%\""
        query = f"SELECT * FROM words WHERE {enhanced_where}"
        # execute...
        pass


def example_integration_distributed():
    """
    Example: If you have multiple query functions scattered
    """
    
    # Define filter constant at top of file
    APOSTROPHE_FILTER = "AND word NOT LIKE \"'%\" "
    
    # Then add to each query:
    
    def select_uncommon(k3):
        query = f"SELECT * FROM words WHERE k3 = ? {APOSTROPHE_FILTER} LIMIT 100"
        # ...
    
    def select_slant(k1):
        query = f"SELECT * FROM words WHERE k1 = ? {APOSTROPHE_FILTER} LIMIT 100"
        # ...
    
    def select_multiword(k2):
        query = f"""
            SELECT * FROM words 
            WHERE k2 = ? 
              AND word LIKE '% %' 
              {APOSTROPHE_FILTER}
            LIMIT 50
        """
        # ...


def example_integration_postfilter():
    """
    Example: If you can't modify queries, filter results after
    """
    
    def search_rhymes(word):
        # Get results (including apostrophe words)
        results = database_query(word)
        
        # Filter out apostrophe words
        cleaned_results = filter_apostrophe_words(results)
        
        return cleaned_results


# ============================================================================
# TESTING & VALIDATION
# ============================================================================

def test_apostrophe_filtering(db_path):
    """
    Test that apostrophe filtering works correctly
    """
    import sqlite3
    
    print("=== TESTING APOSTROPHE FILTERING ===\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test 1: Count apostrophe words BEFORE filtering
    cursor.execute("SELECT COUNT(*) FROM words WHERE word LIKE \"'%\"")
    count_before = cursor.fetchone()[0]
    print(f"1. Apostrophe words in database: {count_before}")
    
    # Test 2: Sample query WITHOUT filter
    cursor.execute("SELECT word FROM words WHERE k1 = 'AA' LIMIT 10")
    unfiltered = [row[0] for row in cursor.fetchall()]
    apostrophe_in_unfiltered = [w for w in unfiltered if w.startswith("'")]
    print(f"2. Unfiltered query returned {len(apostrophe_in_unfiltered)} apostrophe words")
    if apostrophe_in_unfiltered:
        print(f"   Examples: {apostrophe_in_unfiltered}")
    
    # Test 3: Sample query WITH filter
    cursor.execute("SELECT word FROM words WHERE k1 = 'AA' AND word NOT LIKE \"'%\" LIMIT 10")
    filtered = [row[0] for row in cursor.fetchall()]
    apostrophe_in_filtered = [w for w in filtered if w.startswith("'")]
    print(f"3. Filtered query returned {len(apostrophe_in_filtered)} apostrophe words")
    
    # Test 4: Verify no apostrophes in filtered results
    success = len(apostrophe_in_filtered) == 0
    print(f"\n✅ Filter test: {'PASSED' if success else 'FAILED'}")
    
    conn.close()
    
    return success


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print(__doc__)
    print("\n" + "="*70)
    print("APOSTROPHE WORD FILTER - Multiple Implementation Options")
    print("="*70)
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        
        print(f"\nTesting with database: {db_path}\n")
        
        # Run tests
        test_apostrophe_filtering(db_path)
        
        # Show what would be cleaned
        print("\n" + "="*70)
        clean_database_apostrophe_words(db_path, dry_run=True)
        
    else:
        print("\nUsage:")
        print("  python fix_2_apostrophe_filter.py <path_to_database>")
        print("\nExample:")
        print("  python fix_2_apostrophe_filter.py data/words_index.sqlite")
        print("\nThis will:")
        print("  1. Test apostrophe filtering")
        print("  2. Show statistics on apostrophe words")
        print("  3. Display what would be cleaned (dry run)")
