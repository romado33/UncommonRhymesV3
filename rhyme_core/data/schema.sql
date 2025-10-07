-- words_index.sqlite
CREATE TABLE IF NOT EXISTS words(
  word   TEXT PRIMARY KEY,
  pron   TEXT NOT NULL,
  stress TEXT NOT NULL,
  syls   INTEGER NOT NULL,
  k1     TEXT NOT NULL,
  k2     TEXT NOT NULL,
  k3     TEXT NOT NULL,
  zipf   REAL
);
CREATE INDEX IF NOT EXISTS idx_words_k1   ON words(k1);
CREATE INDEX IF NOT EXISTS idx_words_k2   ON words(k2);
CREATE INDEX IF NOT EXISTS idx_words_k3   ON words(k3);
CREATE INDEX IF NOT EXISTS idx_words_zipf ON words(zipf);

-- patterns.sqlite (public derived)
CREATE TABLE IF NOT EXISTS patterns(
  pattern_key TEXT,
  n           INTEGER,
  words       TEXT,
  rhyme_key   TEXT,
  count       INTEGER,
  examples    TEXT
);
CREATE INDEX IF NOT EXISTS idx_patterns_key_n ON patterns(rhyme_key, n);

-- private rap DB (mirror of your big file)
CREATE TABLE IF NOT EXISTS song_rhyme_patterns(
  id INTEGER PRIMARY KEY,
  pattern TEXT,
  source_word TEXT,
  target_word TEXT,
  artist TEXT,
  song_title TEXT,
  album TEXT,
  year INTEGER,
  genre TEXT,
  secondary_genres TEXT,
  line_distance INTEGER,
  pattern_type TEXT,
  confidence_score REAL,
  rhyme_density REAL,
  source_context TEXT,
  target_context TEXT,
  phonetic_similarity REAL,
  cultural_significance REAL,
  language TEXT,
  source_line_index INTEGER,
  target_line_index INTEGER,
  deduplication_hash TEXT,
  source_file TEXT,
  created_timestamp TEXT
);
CREATE INDEX IF NOT EXISTS idx_srp_source_word ON song_rhyme_patterns(source_word);
CREATE INDEX IF NOT EXISTS idx_srp_target_word ON song_rhyme_patterns(target_word);
CREATE INDEX IF NOT EXISTS idx_srp_year        ON song_rhyme_patterns(year);
CREATE INDEX IF NOT EXISTS idx_srp_type        ON song_rhyme_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_srp_dedup       ON song_rhyme_patterns(deduplication_hash);
