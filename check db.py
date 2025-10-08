import sqlite3

# Connect to the database
conn = sqlite3.connect('data/dev/words_index.sqlite')
cursor = conn.cursor()

# Get table names
print("=== TABLES IN DATABASE ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n=== SCHEMA ===")
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    schema = cursor.fetchone()
    print(f"\n{table_name}:")
    print(schema[0])

# Check word count
print("\n=== WORD COUNT ===")
cursor.execute("SELECT COUNT(*) FROM words;")
count = cursor.fetchone()
print(f"Total words in database: {count[0]:,}")

# Look for 'double' and its rhymes
print("\n=== SEARCHING FOR 'double' ===")
cursor.execute("SELECT * FROM words WHERE word = 'double';")
double = cursor.fetchone()
if double:
    print(f"Found 'double': {double}")
else:
    print("'double' not found in database")

print("\n=== SEARCHING FOR RHYMES (trouble, bubble, rubble) ===")
for word in ['trouble', 'bubble', 'rubble', 'stubble']:
    cursor.execute("SELECT * FROM words WHERE word = ?;", (word,))
    result = cursor.fetchone()
    if result:
        print(f"  ✓ {word}: {result}")
    else:
        print(f"  ✗ {word}: NOT FOUND")

# Check what columns exist and sample data
print("\n=== SAMPLE DATA (first 5 rows) ===")
cursor.execute("SELECT * FROM words LIMIT 5;")
rows = cursor.fetchall()
# Get column names
cursor.execute("PRAGMA table_info(words);")
columns = [col[1] for col in cursor.fetchall()]
print(f"Columns: {columns}")
for row in rows:
    print(f"  {row}")

# Check if there's a zipf column and its range
if 'zipf' in columns:
    print("\n=== ZIPF SCORE ANALYSIS ===")
    cursor.execute("SELECT MIN(zipf), MAX(zipf), AVG(zipf) FROM words;")
    zipf_stats = cursor.fetchone()
    print(f"Zipf scores - Min: {zipf_stats[0]:.2f}, Max: {zipf_stats[1]:.2f}, Avg: {zipf_stats[2]:.2f}")
    
    cursor.execute("SELECT COUNT(*) FROM words WHERE zipf <= 4.0;")
    count_under_4 = cursor.fetchone()[0]
    print(f"Words with zipf ≤ 4.0: {count_under_4:,}")
    
    cursor.execute("SELECT COUNT(*) FROM words WHERE zipf <= 6.0;")
    count_under_6 = cursor.fetchone()[0]
    print(f"Words with zipf ≤ 6.0: {count_under_6:,}")

conn.close()
print("\n=== DONE ===")