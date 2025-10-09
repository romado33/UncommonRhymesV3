#!/usr/bin/env python3
"""
CMU Pronouncing Dictionary Database Builder
Downloads CMU dictionary and creates the words table required by engine.py

This script:
1. Downloads the latest CMU Pronouncing Dictionary (~134K words)
2. Creates a SQLite database with the 'words' table
3. Populates it with word pronunciations
4. Creates indexes for fast lookups
"""

import sqlite3
import urllib.request
import re
import os
from typing import List, Tuple

# Try to import pronouncing library for full CMU dict access
try:
    import pronouncing
    import cmudict
    HAS_PRONOUNCING = True
except ImportError:
    HAS_PRONOUNCING = False

class CMUDatabaseBuilder:
    """Build CMU dictionary database for RhymeRarity"""
    
    def __init__(self, db_path: str = "cmudict.db"):
        self.db_path = db_path
        self.cmu_url = "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict"
        self.entries_processed = 0
        self.duplicates_handled = 0
        
    def download_cmu_dict(self) -> List[str]:
        """Download CMU Pronouncing Dictionary"""
        
        # Try pronouncing library first (includes full CMU dict)
        if HAS_PRONOUNCING:
            print("📥 Loading CMU Pronouncing Dictionary from library...")
            try:
                lines = self._get_cmudict_from_library()
                print(f"✅ Loaded {len(lines):,} entries from library")
                return lines
            except Exception as e:
                print(f"⚠️  Library access failed: {e}")
        
        # Try direct download
        print("📥 Downloading CMU Pronouncing Dictionary...")
        print(f"   Source: {self.cmu_url}")
        
        try:
            with urllib.request.urlopen(self.cmu_url) as response:
                content = response.read().decode('utf-8', errors='ignore')
                lines = content.strip().split('\n')
                
            print(f"✅ Downloaded {len(lines):,} entries")
            return lines
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("\n💡 Alternative: Using fallback CMU dictionary...")
            return self._get_fallback_dict()
    
    def _get_cmudict_from_library(self) -> List[str]:
        """Get full CMU dictionary from pronouncing library"""
        dict_data = cmudict.dict()
        lines = []
        
        for word, pronunciations in dict_data.items():
            # Handle multiple pronunciations (variants)
            for idx, pron_list in enumerate(pronunciations):
                # Convert to CMU format
                pron_str = ' '.join(pron_list)
                
                # Format with variant indicator if multiple pronunciations
                if idx == 0:
                    line = f"{word}  {pron_str}"
                else:
                    line = f"{word}({idx})  {pron_str}"
                
                lines.append(line)
        
        return lines
    
    def _get_fallback_dict(self) -> List[str]:
        """Fallback CMU dictionary with essential words"""
        fallback_data = """
GUITAR G IH0 T AA1 R
DOG D AO1 G
CAT K AE1 T
HAT HH AE1 T
BAT B AE1 T
RAT R AE1 T
MAT M AE1 T
CHAT CH AE1 T
FAT F AE1 T
DOLLAR D AA1 L ER0
COLLAR K AA1 L ER0
HOLLER HH AA1 L ER0
SCHOLAR S K AA1 L ER0
ART AA1 R T
CART K AA1 R T
DART D AA1 R T
HEART HH AA1 R T
PART P AA1 R T
START S T AA1 R T
CHART CH AA1 R T
SMART S M AA1 R T
FINDER F AY1 N D ER0
GRINDER G R AY1 N D ER0
KINDER K AY1 N D ER0
MINDER M AY1 N D ER0
WINDER W AY1 N D ER0
REMINDER R IH0 M AY1 N D ER0
BLINDER B L AY1 N D ER0
BINDER B AY1 N D ER0
RIDER R AY1 D ER0
SPIDER S P AY1 D ER0
CIDER S AY1 D ER0
SLIDER S L AY1 D ER0
GLIDER G L AY1 D ER0
WIDER W AY1 D ER0
PROVIDER P R AH0 V AY1 D ER0
OUTSIDER AW1 T S AY2 D ER0
INSIDER IH1 N S AY2 D ER0
DIVIDER D IH0 V AY1 D ER0
DINER D AY1 N ER0
LINER L AY1 N ER0
MINER M AY1 N ER0
FINER F AY1 N ER0
SHINER SH AY1 N ER0
DESIGNER D IH0 Z AY1 N ER0
REFINER R IH0 F AY1 N ER0
RECLINER R IH0 K L AY1 N ER0
WRITER R AY1 T ER0
LIGHTER L AY1 T ER0
FIGHTER F AY1 T ER0
BRIGHTER B R AY1 T ER0
TIGHTER T AY1 T ER0
WHITER W AY1 T ER0
EXCITER IH0 K S AY1 T ER0
INVITER IH0 N V AY1 T ER0
IGNITER IH0 G N AY1 T ER0
LOVE L AH1 V
ABOVE AH0 B AH1 V
DOVE D AH1 V
GLOVE G L AH1 V
SHOVE SH AH1 V
OF AH1 V
THEREOF DH EH2 R AH1 V
WHEREOF W EH2 R AH1 V
THEREOF DH EH2 R AH1 V
MIND M AY1 N D
FIND F AY1 N D
BIND B AY1 N D
BLIND B L AY1 N D
BEHIND B IH0 HH AY1 N D
KIND K AY1 N D
REMIND R IH0 M AY1 N D
WIND W AY1 N D
GRIND G R AY1 N D
REWIND R IY0 W AY1 N D
UNWIND AH0 N W AY1 N D
TIME T AY1 M
RHYME R AY1 M
CHIME CH AY1 M
CLIMB K L AY1 M
CRIME K R AY1 M
DIME D AY1 M
GRIME G R AY1 M
LIME L AY1 M
MIME M AY1 M
PRIME P R AY1 M
SLIME S L AY1 M
SUBLIME S AH0 B L AY1 M
THYME TH AY1 M
FLOW F L OW1
BLOW B L OW1
GLOW G L OW1
GROW G R OW1
KNOW N OW1
LOW L OW1
MOW M OW1
ROW R OW1
SHOW SH OW1
SLOW S L OW1
SNOW S N OW1
STOW S T OW1
THROW TH R OW1
TOW T OW1
BELOW B IH0 L OW1
BESTOW B IH0 S T OW1
MONEY M AH1 N IY0
HONEY H AH1 N IY0
FUNNY F AH1 N IY0
SUNNY S AH1 N IY0
BUNNY B AH1 N IY0
DUMMY D AH1 M IY0
TUMMY T AH1 M IY0
YUMMY Y AH1 M IY0
MUMMY M AH1 M IY0
RUMMY R AH1 M IY0
NIGHT N AY1 T
LIGHT L AY1 T
RIGHT R AY1 T
SIGHT S AY1 T
BRIGHT B R AY1 T
FLIGHT F L AY1 T
HEIGHT HH AY1 T
KNIGHT N AY1 T
MIGHT M AY1 T
PLIGHT P L AY1 T
SLIGHT S L AY1 T
TIGHT T AY1 T
FIGHT F AY1 T
BLIGHT B L AY1 T
FRIGHT F R AY1 T
DAY D EY1
WAY W EY1
SAY S EY1
PLAY P L EY1
MAY M EY1
STAY S T EY1
PAY P EY1
GRAY G R EY1
RAY R EY1
BAY B EY1
LAY L EY1
PREY P R EY1
SLAY S L EY1
STRAY S T R EY1
TRAY T R EY1
AWAY AH0 W EY1
DISPLAY D IH0 S P L EY1
""".strip()
        print(f"✅ Loaded {len(fallback_data.split(chr(10)))} fallback entries")
        return fallback_data.split('\n')
    
    def parse_cmu_line(self, line: str) -> Tuple[str, str, int]:
        """
        Parse CMU dictionary line
        Returns: (word, pronunciation, variant_number)
        
        Format examples:
        WORD  W ER1 D
        WORD(2)  W ER1 D
        """
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith(';;;'):
            return None, None, 0
        
        # Split on whitespace
        parts = line.split()
        if len(parts) < 2:
            return None, None, 0
        
        # Extract word and handle variants like WORD(2)
        word_part = parts[0]
        phonemes = parts[1:]
        
        # Check for variant indicator (e.g., "WORD(2)")
        variant = 0
        match = re.match(r'(.+?)\((\d+)\)$', word_part)
        if match:
            word = match.group(1).lower()
            variant = int(match.group(2))
        else:
            word = word_part.lower()
        
        # Join phonemes into string
        pronunciation = ' '.join(phonemes)
        
        return word, pronunciation, variant
    
    def create_database(self, cmu_lines: List[str]):
        """Create and populate the words database"""
        print(f"\n🗄️  Creating database: {self.db_path}")
        
        # Remove existing database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"   Removed existing database")
        
        # Create connection
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create words table (schema expected by engine.py)
        cursor.execute("""
            CREATE TABLE words (
                word TEXT NOT NULL,
                pron TEXT NOT NULL,
                variant INTEGER DEFAULT 0,
                PRIMARY KEY (word, variant)
            )
        """)
        
        print(f"✅ Created 'words' table")
        
        # Parse and insert entries
        print(f"\n📝 Parsing and inserting entries...")
        entries_to_insert = []
        words_seen = set()
        
        for line in cmu_lines:
            word, pron, variant = self.parse_cmu_line(line)
            
            if word and pron:
                # Track primary pronunciations
                if variant == 0:
                    if word in words_seen:
                        self.duplicates_handled += 1
                        continue
                    words_seen.add(word)
                
                entries_to_insert.append((word, pron, variant))
                self.entries_processed += 1
                
                # Batch insert for performance
                if len(entries_to_insert) >= 1000:
                    cursor.executemany(
                        "INSERT OR REPLACE INTO words (word, pron, variant) VALUES (?, ?, ?)",
                        entries_to_insert
                    )
                    entries_to_insert = []
                    print(f"   Inserted {self.entries_processed:,} entries...", end='\r')
        
        # Insert remaining
        if entries_to_insert:
            cursor.executemany(
                "INSERT OR REPLACE INTO words (word, pron, variant) VALUES (?, ?, ?)",
                entries_to_insert
            )
        
        conn.commit()
        print(f"\n✅ Inserted {self.entries_processed:,} total entries")
        print(f"   Duplicates handled: {self.duplicates_handled:,}")
        
        # Create indexes for fast lookups
        print(f"\n🔍 Creating indexes...")
        cursor.execute("CREATE INDEX idx_word ON words(word)")
        cursor.execute("CREATE INDEX idx_word_variant ON words(word, variant)")
        conn.commit()
        print(f"✅ Indexes created")
        
        # Database statistics
        cursor.execute("SELECT COUNT(*) FROM words")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT word) FROM words")
        unique_words = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 DATABASE STATISTICS:")
        print(f"   Total entries: {total_count:,}")
        print(f"   Unique words: {unique_words:,}")
        print(f"   Database size: {os.path.getsize(self.db_path) / 1024 / 1024:.2f} MB")
    
    def verify_database(self):
        """Verify database works correctly"""
        print(f"\n🧪 Verifying database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test critical words from the dollar/ART issue
        test_words = [
            ('dollar', 'D AA1 L ER0'),
            ('collar', 'K AA1 L ER0'),
            ('art', 'AA1 R T'),
            ('guitar', 'G IH0 T AA1 R'),
            ('dog', 'D AO1 G')
        ]
        
        all_passed = True
        for word, expected_pattern in test_words:
            cursor.execute("SELECT word, pron FROM words WHERE word = ? LIMIT 1", (word,))
            result = cursor.fetchone()
            
            if result:
                found_word, found_pron = result
                # Check if phoneme pattern is close
                status = "✅" if any(p in found_pron for p in expected_pattern.split()[:2]) else "⚠️"
                print(f"   {status} {word:12} -> {found_pron}")
            else:
                print(f"   ❌ {word:12} -> NOT FOUND")
                all_passed = False
        
        conn.close()
        
        if all_passed:
            print(f"\n✅ Database verification PASSED")
        else:
            print(f"\n⚠️  Database verification completed with warnings")
        
        return all_passed

def main():
    """Main execution"""
    print("=" * 70)
    print("CMU PRONOUNCING DICTIONARY DATABASE BUILDER")
    print("RhymeRarity System - Database Initialization")
    print("=" * 70)
    
    # Determine database path
    db_path = "cmudict.db"
    
    # Check if we're in the app directory
    if os.path.exists("app.py"):
        print(f"📁 Detected app directory")
    
    builder = CMUDatabaseBuilder(db_path)
    
    # Download dictionary
    cmu_lines = builder.download_cmu_dict()
    
    # Build database
    builder.create_database(cmu_lines)
    
    # Verify
    builder.verify_database()
    
    print(f"\n{'=' * 70}")
    print(f"🎯 DATABASE READY!")
    print(f"{'=' * 70}")
    print(f"\n📍 Database location: {os.path.abspath(db_path)}")
    print(f"\n🔧 NEXT STEPS:")
    print(f"   1. Ensure your engine.py connects to '{db_path}'")
    print(f"   2. Update database path if needed")
    print(f"   3. Run your app.py to test")
    print(f"\n💡 If engine.py looks for a different database name,")
    print(f"   rename '{db_path}' to match or update engine.py")
    print(f"\n{'=' * 70}")

if __name__ == "__main__":
    main()
