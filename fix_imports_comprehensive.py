#!/usr/bin/env python3
"""
🔧 RhymeRarity Import Structure Fixer & Diagnostic Tool
Fixes the "No module named 'engine'" error by setting up proper package structure

This script:
1. Diagnoses your current project structure
2. Creates the proper Python package layout  
3. Moves files to correct locations
4. Creates necessary __init__.py files
5. Validates the setup

Run this from your project root: python fix_imports_comprehensive.py
"""

import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Dict

class ImportStructureFixer:
    """Comprehensive import structure diagnostic and fixer"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.errors = []
        self.warnings = []
        self.actions_taken = []
        
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def print_section(self, text: str):
        """Print formatted section"""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}")
    
    def find_python_files(self) -> Dict[str, List[Path]]:
        """Find all relevant Python files in the project"""
        files = {
            'search': [],
            'phonetics': [],
            'benchmark': [],
            'paths': [],
            'rap': [],
            'engine': [],
            'app': [],
            'init': [],
            'other': []
        }
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip venv, __pycache__, etc.
            if any(skip in str(py_file) for skip in ['.venv', 'venv', '__pycache__', 'site-packages']):
                continue
                
            name = py_file.stem
            if name == 'search':
                files['search'].append(py_file)
            elif name == 'phonetics':
                files['phonetics'].append(py_file)
            elif name == 'benchmark':
                files['benchmark'].append(py_file)
            elif name == 'paths':
                files['paths'].append(py_file)
            elif name == 'rap':
                files['rap'].append(py_file)
            elif name == 'engine':
                files['engine'].append(py_file)
            elif name == 'app':
                files['app'].append(py_file)
            elif name == '__init__':
                files['init'].append(py_file)
            else:
                files['other'].append(py_file)
        
        return files
    
    def diagnose_structure(self) -> bool:
        """Diagnose current project structure"""
        self.print_header("📊 DIAGNOSING PROJECT STRUCTURE")
        
        print(f"\n📁 Project Root: {self.project_root}")
        
        # Find all Python files
        files = self.find_python_files()
        
        self.print_section("Python Files Found")
        
        for category, paths in files.items():
            if paths:
                print(f"\n{category.upper()}:")
                for p in paths:
                    rel_path = p.relative_to(self.project_root)
                    print(f"  ✓ {rel_path}")
        
        # Check for required files
        self.print_section("Required Files Check")
        
        has_search = bool(files['search'])
        has_phonetics = bool(files['phonetics'])
        has_benchmark = bool(files['benchmark'])
        
        print(f"{'✅' if has_search else '❌'} search.py - {'Found' if has_search else 'MISSING'}")
        print(f"{'✅' if has_phonetics else '❌'} phonetics.py - {'Found' if has_phonetics else 'MISSING'}")
        print(f"{'✅' if has_benchmark else '❌'} benchmark.py - {'Found' if has_benchmark else 'MISSING'}")
        
        if not has_search:
            self.errors.append("search.py not found - this is required!")
        if not has_phonetics:
            self.warnings.append("phonetics.py not found - may cause import errors")
        if not has_benchmark:
            self.warnings.append("benchmark.py not found - can't run benchmarks")
        
        # Check package structure
        self.print_section("Package Structure Check")
        
        rhyme_core = self.project_root / "rhyme_core"
        rhyme_core_exists = rhyme_core.exists() and rhyme_core.is_dir()
        
        print(f"{'✅' if rhyme_core_exists else '❌'} rhyme_core/ directory - {'Found' if rhyme_core_exists else 'MISSING'}")
        
        if rhyme_core_exists:
            init_file = rhyme_core / "__init__.py"
            has_init = init_file.exists()
            print(f"{'✅' if has_init else '❌'} rhyme_core/__init__.py - {'Found' if has_init else 'MISSING'}")
            
            data_dir = rhyme_core / "data"
            data_exists = data_dir.exists() and data_dir.is_dir()
            print(f"{'✅' if data_exists else '❌'} rhyme_core/data/ directory - {'Found' if data_exists else 'MISSING'}")
            
            if data_exists:
                data_init = data_dir / "__init__.py"
                has_data_init = data_init.exists()
                print(f"{'✅' if has_data_init else '❌'} rhyme_core/data/__init__.py - {'Found' if has_data_init else 'MISSING'}")
        
        return not bool(self.errors)
    
    def create_package_structure(self, dry_run: bool = False) -> bool:
        """Create proper Python package structure"""
        self.print_header("🏗️  CREATING PACKAGE STRUCTURE")
        
        # Define required structure
        rhyme_core = self.project_root / "rhyme_core"
        data_dir = rhyme_core / "data"
        tests_dir = self.project_root / "tests"
        
        actions = []
        
        # Create rhyme_core directory
        if not rhyme_core.exists():
            actions.append(("mkdir", rhyme_core))
            
        # Create rhyme_core/__init__.py
        init_file = rhyme_core / "__init__.py"
        if not init_file.exists():
            actions.append(("touch", init_file, "rhyme_core package init"))
        
        # Create data directory
        if not data_dir.exists():
            actions.append(("mkdir", data_dir))
        
        # Create data/__init__.py
        data_init = data_dir / "__init__.py"
        if not data_init.exists():
            actions.append(("touch", data_init, "data package init"))
        
        # Create tests directory if needed
        if not tests_dir.exists():
            actions.append(("mkdir", tests_dir))
        
        # Show what will be done
        if actions:
            self.print_section("Actions to Perform")
            for action in actions:
                if action[0] == "mkdir":
                    print(f"  📁 Create directory: {action[1].relative_to(self.project_root)}")
                elif action[0] == "touch":
                    print(f"  📄 Create file: {action[1].relative_to(self.project_root)}")
                    if len(action) > 2:
                        print(f"     └─ {action[2]}")
        else:
            print("\n✅ Package structure already exists!")
            return True
        
        # Execute actions
        if not dry_run:
            self.print_section("Executing Actions")
            for action in actions:
                try:
                    if action[0] == "mkdir":
                        action[1].mkdir(parents=True, exist_ok=True)
                        print(f"  ✓ Created: {action[1].relative_to(self.project_root)}")
                        self.actions_taken.append(f"Created directory: {action[1]}")
                    elif action[0] == "touch":
                        action[1].touch()
                        print(f"  ✓ Created: {action[1].relative_to(self.project_root)}")
                        self.actions_taken.append(f"Created file: {action[1]}")
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    self.errors.append(f"Failed to create {action[1]}: {e}")
                    return False
        else:
            print("\n⚠️  DRY RUN - No changes made")
        
        return True
    
    def move_files_to_package(self, dry_run: bool = False) -> bool:
        """Move Python files to correct package locations"""
        self.print_header("📦 ORGANIZING FILES INTO PACKAGE")
        
        files = self.find_python_files()
        rhyme_core = self.project_root / "rhyme_core"
        data_dir = rhyme_core / "data"
        tests_dir = self.project_root / "tests"
        
        moves = []
        
        # search.py → rhyme_core/
        for search_file in files['search']:
            if search_file.parent != rhyme_core:
                moves.append((search_file, rhyme_core / "search.py"))
        
        # phonetics.py → rhyme_core/
        for phonetics_file in files['phonetics']:
            if phonetics_file.parent != rhyme_core:
                moves.append((phonetics_file, rhyme_core / "phonetics.py"))
        
        # rap.py → rhyme_core/ (if exists)
        for rap_file in files['rap']:
            if rap_file.parent != rhyme_core:
                moves.append((rap_file, rhyme_core / "rap.py"))
        
        # paths.py → rhyme_core/data/
        for paths_file in files['paths']:
            if paths_file.parent != data_dir:
                moves.append((paths_file, data_dir / "paths.py"))
        
        # benchmark.py → tests/
        for benchmark_file in files['benchmark']:
            if benchmark_file.parent != tests_dir:
                moves.append((benchmark_file, tests_dir / "benchmark.py"))
        
        # engine.py → rhyme_core/ (if exists)
        for engine_file in files['engine']:
            if engine_file.parent != rhyme_core:
                moves.append((engine_file, rhyme_core / "engine.py"))
        
        if not moves:
            print("\n✅ All files are already in correct locations!")
            return True
        
        # Show planned moves
        self.print_section("Files to Move")
        for src, dst in moves:
            src_rel = src.relative_to(self.project_root)
            dst_rel = dst.relative_to(self.project_root)
            print(f"  📄 {src_rel}")
            print(f"     └─→ {dst_rel}")
        
        # Execute moves
        if not dry_run:
            self.print_section("Moving Files")
            for src, dst in moves:
                try:
                    # Create destination directory if needed
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(src), str(dst))
                    
                    src_rel = src.relative_to(self.project_root)
                    dst_rel = dst.relative_to(self.project_root)
                    print(f"  ✓ Moved: {src_rel} → {dst_rel}")
                    self.actions_taken.append(f"Moved: {src} → {dst}")
                except Exception as e:
                    print(f"  ✗ Failed to move {src}: {e}")
                    self.errors.append(f"Failed to move {src}: {e}")
                    return False
        else:
            print("\n⚠️  DRY RUN - No files moved")
        
        return True
    
    def create_init_files(self) -> bool:
        """Create comprehensive __init__.py files with proper imports"""
        self.print_header("📝 CREATING __INIT__.PY FILES")
        
        rhyme_core = self.project_root / "rhyme_core"
        data_dir = rhyme_core / "data"
        
        # rhyme_core/__init__.py
        init_content = '''"""
RhymeRarity - Anti-LLM Rhyme Engine
Advanced phonetic analysis and rare rhyme generation
"""

try:
    from .search import search_all_categories, search_rhymes
    from .phonetics import parse_pron, k_keys, extract_stress
except ImportError as e:
    print(f"Warning: Could not import rhyme_core modules: {e}")
    # Provide fallback None values
    search_all_categories = None
    search_rhymes = None

__version__ = "1.0.0"
__all__ = ['search_all_categories', 'search_rhymes']
'''
        
        # data/__init__.py  
        data_init_content = '''"""
RhymeRarity Data Package
Database paths and configuration
"""

try:
    from .paths import words_db, get_db_path
except ImportError:
    words_db = None
    get_db_path = None

__all__ = ['words_db', 'get_db_path']
'''
        
        try:
            # Write rhyme_core/__init__.py
            init_file = rhyme_core / "__init__.py"
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(init_content)
            print(f"✓ Created: rhyme_core/__init__.py")
            self.actions_taken.append("Created rhyme_core/__init__.py with imports")
            
            # Write data/__init__.py
            data_init_file = data_dir / "__init__.py"
            with open(data_init_file, 'w', encoding='utf-8') as f:
                f.write(data_init_content)
            print(f"✓ Created: rhyme_core/data/__init__.py")
            self.actions_taken.append("Created rhyme_core/data/__init__.py with imports")
            
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.errors.append(f"Failed to create __init__.py files: {e}")
            return False
    
    def validate_setup(self) -> bool:
        """Validate that the package structure is correct"""
        self.print_header("✅ VALIDATING SETUP")
        
        rhyme_core = self.project_root / "rhyme_core"
        data_dir = rhyme_core / "data"
        
        checks = [
            (rhyme_core.exists(), "rhyme_core/ directory exists"),
            ((rhyme_core / "__init__.py").exists(), "rhyme_core/__init__.py exists"),
            ((rhyme_core / "search.py").exists(), "rhyme_core/search.py exists"),
            (data_dir.exists(), "rhyme_core/data/ directory exists"),
            ((data_dir / "__init__.py").exists(), "rhyme_core/data/__init__.py exists"),
        ]
        
        all_passed = True
        for passed, description in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {description}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def print_next_steps(self):
        """Print what the user should do next"""
        self.print_header("🚀 NEXT STEPS")
        
        print("\n1️⃣  Test the import structure:")
        print("   python -c \"from rhyme_core import search_all_categories; print('✅ Imports working!')\"")
        
        print("\n2️⃣  Run the benchmark:")
        print("   python tests/benchmark.py")
        
        print("\n3️⃣  If you still get import errors:")
        print("   - Make sure you're running from the project root directory")
        print("   - Check that rhyme_core/data/paths.py has correct database paths")
        print("   - Verify your Python path includes the project root")
        
        print("\n4️⃣  Expected directory structure:")
        print("""
   uncommonrhymesv3/
   ├── rhyme_core/              # Python package
   │   ├── __init__.py          # Package init
   │   ├── search.py            # Main search module
   │   ├── phonetics.py         # Phonetics utilities
   │   ├── data/                # Data sub-package
   │   │   ├── __init__.py      # Data package init
   │   │   └── paths.py         # Database paths
   │   └── ...
   ├── tests/
   │   └── benchmark.py         # Benchmark script
   └── data/
       └── words_index.sqlite   # Database
        """)
    
    def print_summary(self):
        """Print summary of what was done"""
        self.print_header("📊 SUMMARY")
        
        if self.actions_taken:
            print("\n✅ Actions Taken:")
            for action in self.actions_taken:
                print(f"  • {action}")
        else:
            print("\n⚠️  No actions were taken - structure may already be correct")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  • {error}")
            print("\n⚠️  Fix these errors before running benchmark!")
        else:
            print("\n✅ No errors - structure should be ready!")
    
    def run(self, dry_run: bool = False, auto_fix: bool = True):
        """Run the complete diagnostic and fix process"""
        print("🔧 RhymeRarity Import Structure Fixer")
        print("====================================")
        
        # Step 1: Diagnose
        structure_ok = self.diagnose_structure()
        
        if structure_ok and not auto_fix:
            print("\n✅ Structure looks good! No fixes needed.")
            self.print_next_steps()
            return
        
        # Step 2: Ask for confirmation unless auto_fix
        if not dry_run and not auto_fix:
            response = input("\n❓ Apply fixes? (y/n): ").lower().strip()
            if response != 'y':
                print("❌ Cancelled - no changes made")
                return
        
        # Step 3: Create package structure
        if not self.create_package_structure(dry_run=dry_run):
            print("❌ Failed to create package structure")
            return
        
        # Step 4: Move files
        if not self.move_files_to_package(dry_run=dry_run):
            print("❌ Failed to move files")
            return
        
        # Step 5: Create __init__.py files
        if not dry_run:
            self.create_init_files()
        
        # Step 6: Validate
        if not dry_run:
            if self.validate_setup():
                print("\n✅ Package structure validated successfully!")
            else:
                print("\n⚠️  Validation found issues - check the output above")
        
        # Step 7: Print summary and next steps
        self.print_summary()
        if not dry_run:
            self.print_next_steps()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fix RhymeRarity import structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be done)
  python fix_imports_comprehensive.py --dry-run
  
  # Apply fixes automatically
  python fix_imports_comprehensive.py --auto-fix
  
  # Interactive mode (ask before making changes)
  python fix_imports_comprehensive.py
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--auto-fix', action='store_true',
                        help='Automatically apply fixes without asking')
    
    args = parser.parse_args()
    
    fixer = ImportStructureFixer()
    fixer.run(dry_run=args.dry_run, auto_fix=args.auto_fix)


if __name__ == "__main__":
    main()
