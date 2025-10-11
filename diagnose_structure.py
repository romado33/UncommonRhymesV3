#!/usr/bin/env python3
"""
Diagnostic script to check RhymeRarity project structure and fix import issues
"""

import sys
from pathlib import Path

print("=" * 80)
print("RhymeRarity Project Structure Diagnostic")
print("=" * 80)
print()

# Check current directory
current_dir = Path.cwd()
print(f"Current directory: {current_dir}")
print()

# Expected structure
expected_structure = {
    "rhyme_core": {
        "__init__.py": "Package init file",
        "search.py": "Main search module",
        "phonetics.py": "Phonetics utilities",
        "data": {
            "__init__.py": "Data package init",
            "paths.py": "Database path configuration"
        }
    },
    "tests": {
        "benchmark.py": "Benchmark script"
    }
}

print("Checking project structure...")
print("-" * 80)

def check_path(base: Path, structure: dict, prefix=""):
    missing = []
    found = []
    
    for name, desc in structure.items():
        path = base / name
        if isinstance(desc, dict):
            # It's a directory
            if path.is_dir():
                found.append(f"{prefix}{name}/ ✅")
                # Recursively check contents
                sub_missing, sub_found = check_path(path, desc, prefix + "  ")
                missing.extend(sub_missing)
                found.extend(sub_found)
            else:
                missing.append(f"{prefix}{name}/ ❌ (directory)")
        else:
            # It's a file
            if path.is_file():
                found.append(f"{prefix}{name} ✅")
            else:
                missing.append(f"{prefix}{name} ❌ ({desc})")
    
    return missing, found

missing, found = check_path(current_dir, expected_structure)

print("✅ Found:")
for item in found:
    print(f"  {item}")

if missing:
    print()
    print("❌ Missing:")
    for item in missing:
        print(f"  {item}")

print()
print("=" * 80)
print("Diagnosis")
print("=" * 80)

if missing:
    print("❌ Project structure is incomplete!")
    print()
    print("The error 'No module named engine' likely means:")
    print("1. The rhyme_core package structure isn't set up correctly")
    print("2. Python can't find the relative imports in search.py")
    print()
    print("Required structure:")
    print("""
uncommonrhymesv3/
├── rhyme_core/              ← Python package
│   ├── __init__.py          ← Required for package
│   ├── search.py            ← Main search module
│   ├── phonetics.py         ← Phonetics utilities
│   ├── data/                ← Sub-package
│   │   ├── __init__.py      ← Required for sub-package
│   │   └── paths.py         ← Database paths
│   └── ...
└── tests/
    └── benchmark.py         ← Benchmark script
""")
else:
    print("✅ Project structure looks good!")
    print()
    print("If you're still getting import errors, the issue might be:")
    print("1. Missing __init__.py files")
    print("2. Wrong Python path")
    print("3. Missing dependencies")

print()
print("=" * 80)
print("Next Steps")
print("=" * 80)

# Check if files exist in current directory
if (current_dir / "search.py").is_file():
    print()
    print("⚠️  Found search.py in root directory!")
    print("This should be in rhyme_core/ directory.")
    print()
    print("Run this to move files to correct location:")
    print("""
# Create package structure
mkdir -p rhyme_core/data
touch rhyme_core/__init__.py
touch rhyme_core/data/__init__.py

# Move files
mv search.py rhyme_core/
mv phonetics.py rhyme_core/

# Check if you have these files and move them too:
# mv rap.py rhyme_core/  (if exists)
# mv paths.py rhyme_core/data/  (if exists)
""")

elif (current_dir / "rhyme_core" / "search.py").is_file():
    print()
    print("✅ Files are in correct location (rhyme_core/)")
    print()
    
    # Check for __init__.py
    if not (current_dir / "rhyme_core" / "__init__.py").is_file():
        print("❌ Missing rhyme_core/__init__.py")
        print("Run: touch rhyme_core/__init__.py")
        print()
    
    if not (current_dir / "rhyme_core" / "data" / "__init__.py").is_file():
        print("❌ Missing rhyme_core/data/__init__.py")
        print("Run: touch rhyme_core/data/__init__.py")
        print()
    
    print("Try running benchmark again:")
    print("python tests/benchmark.py")

else:
    print()
    print("❌ Cannot find search.py!")
    print("Where are your source files located?")

print()
print("=" * 80)

# Check Python path
print("Python path:")
for p in sys.path[:5]:
    print(f"  {p}")

print()
print("For more help, show me your directory structure:")
print("  Windows: dir /s /b")
print("  Linux/Mac: find . -type f -name '*.py' | head -20")
