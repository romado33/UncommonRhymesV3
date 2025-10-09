#!/usr/bin/env python3
"""
Complete Rhyme Database Builder - Downloads CMU Dict if needed
Builds rhyme.db with full 130,000+ word vocabulary
"""

import sqlite3
import sys
from pathlib import Path

print("=" * 70)
print("COMPLETE RHYME DATABASE BUILDER")
print("=" * 70)
print()

# Check dependencies
print("📦 Checking dependencies:")

try:
    import cmudict
    HAS_CMUDICT = True
    print("   cmudict: ✅ Available")
except ImportError:
    HAS_CMUDICT = False
    print("   cmudict: ❌ Not available")

try:
    import wordfreq
    from wordfreq import zipf_frequency
    HAS_WORDFREQ = True
    print("   wordfreq: ✅ Available")
except ImportError:
    HAS_WORDFREQ = False
    print("   wordfreq: ❌ Not available")
    print()
    print("⚠️  Installing wordfreq...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "wordfreq", "--break-system-packages", "-q"])
    from wordfreq import zipf_frequency
    HAS_WORDFREQ = True
    print("   wordfreq: ✅ Installed successfully")

print()

# Function to download CMU dict
def download_cmu_dict():
    """Download CMU Pronunciation Dictionary from official source"""
    import urllib.request
    
    print("📥 Downloading CMU Pronunciation Dictionary...")
    url = "http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict-0.7b"
    
    try:
        print(f"   Source: {url}")
        response = urllib.request.urlopen(url, timeout=30)
        content = response.read().decode('latin-1')
        
        lines = content.split('\n')
        print(f"   Downloaded {len(lines):,} lines")
        
        # Parse into dictionary
        cmu_data = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';;;'):
                continue
            
            parts = line.split('  ')
            if len(parts) < 2:
                continue
            
            word = parts[0].upper()
            
            # Handle variant pronunciations (e.g., "WORD(1)")
            if '(' in word:
                word = word.split('(')[0]
            
            phonemes = parts[1].strip()
            
            # Store first pronunciation only
            if word not in cmu_data:
                cmu_data[word] = phonemes
        
        print(f"   Parsed {len(cmu_data):,} unique words")
        return cmu_data
        
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return None

# Get CMU dictionary data
print("🔍 Loading pronunciation data...")

if HAS_CMUDICT:
    print("   Using cmudict library")
    d = cmudict.dict()
    cmu_data = {}
    for word, prons in d.items():
        # Take first pronunciation
        cmu_data[word.upper()] = ' '.join(prons[0])
    print(f"   Loaded {len(cmu_data):,} words from cmudict")
else:
    print("   Attempting to download CMU dictionary...")
    cmu_data = download_cmu_dict()
    
    if not cmu_data:
        print()
        print("❌ Could not load CMU dictionary!")
        print()
        print("SOLUTION: Install cmudict library:")
        print("  pip install cmudict")
        print()
        print("Or check your internet connection for automatic download.")
        sys.exit(1)

print()

# Helper functions
def strip_stress(phoneme):
    """Remove stress markers"""
    return phoneme.rstrip('012')

def is_vowel(phoneme):
    """Check if phoneme is a vowel"""
    return phoneme and phoneme[-1] in '012'

def extract_rhyme_keys(phonemes_str):
    """Extract K1, K2, K3 rhyme keys"""
    phonemes = phonemes_str.split()
    
    # Find last stressed vowel
    last_stress_idx = -1
    for i in range(len(phonemes) - 1, -1, -1):
        if phonemes[i][-1] in '12':
            last_stress_idx = i
            break
    
    if last_stress_idx == -1:
        return ("", "", "")
    
    stressed_vowel = phonemes[last_stress_idx]
    tail = phonemes[last_stress_idx + 1:] if last_stress_idx < len(phonemes) - 1 else []
    
    k1 = strip_stress(stressed_vowel)
    k2 = strip_stress(stressed_vowel) + ("|" + " ".join(tail) if tail else "")
    k3 = stressed_vowel + ("|" + " ".join(tail) if tail else "")
    
    return (k1, k2, k3)

def count_syllables(phonemes_str):
    """Count syllables (vowel phonemes)"""
    return sum(1 for p in phonemes_str.split() if is_vowel(p))

def extract_stress_pattern(phonemes_str):
    """Extract stress pattern for meter classification"""
    phonemes = phonemes_str.split()
    pattern = []
    for ph in phonemes:
        if is_vowel(ph):
            pattern.append('1' if ph[-1] in '12' else '0')
    return '-'.join(pattern) if pattern else ''

# Create database
db_path = Path("rhyme.db")
if db_path.exists():
    print(f"🗄️  Removing existing database: {db_path}")
    db_path.unlink()

print(f"🗄️  Creating database: {db_path}")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Create table with ALL required columns
cur.execute("""
    CREATE TABLE words (
        word TEXT PRIMARY KEY,
        pron TEXT NOT NULL,
        k1 TEXT,
        k2 TEXT,
        k3 TEXT,
        zipf REAL DEFAULT 0.0,
        syls INTEGER DEFAULT 1,
        stress TEXT DEFAULT ''
    )
""")

print("✅ Created 'words' table with complete schema")
print()

# Process all words
print(f"📚 Processing {len(cmu_data):,} words...")
print("   (This may take 1-2 minutes...)")

batch_size = 1000
batch_data = []
processed = 0

for word, pron in cmu_data.items():
    # Get zipf score
    if HAS_WORDFREQ:
        zipf = zipf_frequency(word.lower(), 'en')
    else:
        zipf = 3.0  # Default moderate frequency
    
    # Extract rhyme keys
    k1, k2, k3 = extract_rhyme_keys(pron)
    
    # Count syllables
    syls = count_syllables(pron)
    
    # Get stress pattern
    stress = extract_stress_pattern(pron)
    
    batch_data.append((word, pron, k1, k2, k3, zipf, syls, stress))
    
    # Insert in batches
    if len(batch_data) >= batch_size:
        cur.executemany(
            "INSERT OR IGNORE INTO words VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            batch_data
        )
        processed += len(batch_data)
        batch_data = []
        print(f"   Processed {processed:,} words...", end='\r')

# Insert remaining
if batch_data:
    cur.executemany(
        "INSERT OR IGNORE INTO words VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        batch_data
    )
    processed += len(batch_data)

print(f"   Processed {processed:,} words... ✅")
conn.commit()

print()
print("🔍 Creating indexes for fast lookups...")

# Create indexes
cur.execute("CREATE INDEX idx_k1 ON words(k1)")
cur.execute("CREATE INDEX idx_k2 ON words(k2)")
cur.execute("CREATE INDEX idx_k3 ON words(k3)")
cur.execute("CREATE INDEX idx_zipf ON words(zipf)")
cur.execute("CREATE INDEX idx_syls ON words(syls)")
cur.execute("CREATE INDEX idx_stress ON words(stress)")

print("✅ Indexes created")
conn.commit()
print()

# Statistics
cur.execute("SELECT COUNT(*) FROM words")
total_words = cur.fetchone()[0]

cur.execute("SELECT AVG(zipf) FROM words")
avg_zipf = cur.fetchone()[0]

db_size_mb = db_path.stat().st_size / (1024 * 1024)

print("📊 DATABASE STATISTICS:")
print(f"   Total words: {total_words:,}")
print(f"   Average zipf: {avg_zipf:.2f}")
print(f"   Database size: {db_size_mb:.2f} MB")
print()

# Verification tests
print("🧪 Verifying database functionality...")
print()

# Test 1: Basic pronunciation lookup
print("1️⃣  Testing pronunciation lookup:")
test_words = ["GUITAR", "DOG", "DOLLAR", "BED", "ORANGE", "PURPLE"]
for word in test_words:
    cur.execute("SELECT pron FROM words WHERE word = ?", (word,))
    row = cur.fetchone()
    if row:
        print(f"   ✅ {word:12} -> {row[0]}")
    else:
        print(f"   ⚠️  {word:12} -> Not found")

print()

# Test 2: Rhyme key matching
print("2️⃣  Testing rhyme key matching:")
cur.execute("SELECT word, k1, k2, k3 FROM words WHERE word IN ('DOG', 'FOG', 'LOG')")
for word, k1, k2, k3 in cur.fetchall():
    print(f"   {word:12} K1={k1:8} K2={k2:12} K3={k3}")

print()

# Test 3: Dollar/Art separation (critical bug fix verification)
print("3️⃣  Testing Dollar/ART phonetic separation:")
cur.execute("SELECT word, k3 FROM words WHERE word IN ('ART', 'COLLAR', 'DOLLAR', 'CHART', 'SCHOLAR')")
results = cur.fetchall()
for word, k3 in results:
    print(f"   {word:12} -> K3={k3}")

# Verify they're in different families
k3_groups = {}
for word, k3 in results:
    if k3 not in k3_groups:
        k3_groups[k3] = []
    k3_groups[k3].append(word)

print("   Phonetic families:")
for k3, words in k3_groups.items():
    print(f"     {k3}: {words}")

print()

# Test 4: Sample search
print("4️⃣  Testing sample rhyme search:")
cur.execute("""
    SELECT word, k3, syls, zipf 
    FROM words 
    WHERE k3 = (SELECT k3 FROM words WHERE word = 'STAR' LIMIT 1)
    AND word != 'STAR'
    LIMIT 5
""")
print("   Rhymes for 'STAR':")
for word, k3, syls, zipf in cur.fetchall():
    print(f"     {word:12} ({syls} syl, zipf={zipf:.2f})")

conn.close()

print()
print("=" * 70)
print("🎯 DATABASE READY!")
print("=" * 70)
print()
print(f"📍 Database location: {db_path.absolute()}")
print()
print("✅ Database includes:")
print(f"   • {total_words:,} words from CMU Dictionary")
print("   • Complete phonetic pronunciations (ARPAbet)")
print("   • K1, K2, K3 rhyme keys for fast matching")
print("   • Zipf frequency scores")
print("   • Syllable counts and stress patterns")
print("   • Optimized indexes for sub-millisecond queries")
print()
print("🔧 NEXT STEPS:")
print("   1. Copy rhyme.db to your app directory")
print("   2. Run: python app.py")
print("   3. Open: http://127.0.0.1:7860")
print()
print("=" * 70)
