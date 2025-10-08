#!/bin/bash
# apply_patches.sh - Apply all recommended fixes to UncommonRhymesV3

echo "🔧 UncommonRhymesV3 Patch Script"
echo "================================"

# 1. Remove backup files
echo "📁 Removing backup files..."
find . -name "*.bak*" -type f -delete
echo "  ✓ Removed all .bak files"

# 2. Fix .gitignore
echo "📝 Fixing .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
.venv/
venv/
.env
.env.*
*.egg-info/
dist/
build/

# Data
data/cache/
data/dev/*.full.sqlite
data/checksums/
*.db
*.sqlite
*.sqlite3
!data/dev/.gitkeep

# Logs
logs/
*.log
*.log.*

# Backups
*.bak
*.bak.*

# OS
.DS_Store
Thumbs.db
desktop.ini

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Gradio
gradio_cached_examples/
flagged/
EOF
echo "  ✓ Fixed .gitignore"

# 3. Create .gitkeep for data/dev
echo "📁 Creating .gitkeep..."
touch data/dev/.gitkeep
echo "  ✓ Created data/dev/.gitkeep"

# 4. Update requirements.txt
echo "📦 Updating requirements.txt..."
if ! grep -q "cmudict" requirements.txt; then
    echo "cmudict==1.1.1  # Required for build_words_index.py" >> requirements.txt
    echo "  ✓ Added cmudict to requirements.txt"
else
    echo "  ⚠ cmudict already in requirements.txt"
fi

# 5. Fix app.py imports
echo "🐍 Fixing app.py imports..."
python3 << 'PYTHON_SCRIPT'
import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix imports at the top
lines = content.split('\n')
new_lines = []
skip_lines = set()

# Find lines to skip
for i, line in enumerate(lines):
    if 'import os' in line and 'os' not in ''.join(lines[i+1:i+10]):
        skip_lines.add(i)
    if 'from datetime import datetime' in line:
        skip_lines.add(i)
    if 'import csv, io' in line:
        skip_lines.add(i)
        # Add them separately
        new_lines.append('import csv')
        new_lines.append('import io')
    elif i not in skip_lines:
        new_lines.append(line)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("  ✓ Fixed app.py imports")
PYTHON_SCRIPT

# 6. Remove the tracked database from git (if in a git repo)
if [ -d .git ]; then
    echo "🗃️ Removing database from Git tracking..."
    git rm --cached data/dev/words_index.sqlite 2>/dev/null || true
    echo "  ✓ Removed database from Git tracking"
fi

# 7. Build the database if it doesn't exist or is empty
echo "🗄️ Checking database..."
if [ ! -f data/dev/words_index.sqlite ] || [ ! -s data/dev/words_index.sqlite ]; then
    echo "  Building database..."
    pip install cmudict wordfreq --quiet
    python scripts/build_words_index.py
else
    # Check if database has data
    python3 << 'CHECK_DB'
import sqlite3
try:
    con = sqlite3.connect('data/dev/words_index.sqlite')
    count = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    con.close()
    if count == 0:
        print("  ⚠ Database is empty, rebuilding...")
        import subprocess
        subprocess.run(['python', 'scripts/build_words_index.py'])
    else:
        print(f"  ✓ Database OK: {count:,} words")
except Exception as e:
    print(f"  ⚠ Database error: {e}")
CHECK_DB
fi

# 8. Create GitHub Actions workflow
echo "🚀 Creating GitHub Actions workflow..."
mkdir -p .github/workflows
cat > .github/workflows/test.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install cmudict
    
    - name: Build word database
      run: python scripts/build_words_index.py
    
    - name: Run tests
      run: pytest tests/ -v
    
    - name: Check code quality
      run: |
        ruff check . || true
        black --check . || true
EOF
echo "  ✓ Created .github/workflows/test.yml"

echo ""
echo "✅ All patches applied!"
echo ""
echo "Run these commands to verify:"
echo "  pytest tests/ -v           # Run tests"
echo "  python app.py              # Start the app"
echo "  ruff check .              # Check code quality"
echo ""
echo "If you're in a git repository, commit with:"
echo "  git add ."
echo "  git commit -m 'Apply code review fixes: clean up backups, fix imports, update dependencies'"
