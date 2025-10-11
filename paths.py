"""
Database path configuration for RhymeRarity
"""
from pathlib import Path
import os

def words_db() -> Path:
    """
    Return path to words database.
    Searches multiple possible locations.
    """
    # Try locations in priority order
    possible_paths = [
        # 1. Environment variable override
        Path(os.getenv("RHYME_DB_PATH", "")),
        
        # 2. Relative to this file (data/ subdirectory)
        Path(__file__).parent / "words_index.sqlite",
        
        # 3. Project root data/ directory
        Path(__file__).parent.parent.parent / "data" / "words_index.sqlite",
        
        # 4. Current working directory
        Path.cwd() / "data" / "words_index.sqlite",
        
        # 5. Legacy location
        Path.cwd() / "rhyme.db",
        
        # 6. Alternative name
        Path.cwd() / "words.db",
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            return path.resolve()
    
    # Return default path even if doesn't exist
    # (Will give better error message later)
    default = Path(__file__).parent.parent.parent / "data" / "words_index.sqlite"
    return default.resolve()

def rap_db() -> Path:
    """
    Return path to rap/hip-hop database.
    Returns None if not available.
    """
    possible_paths = [
        Path(__file__).parent / "rap.db",
        Path(__file__).parent / "hip_hop.db",
        Path(__file__).parent.parent.parent / "data" / "rap.db",
        Path.cwd() / "data" / "rap.db",
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            return path.resolve()
    
    return None

def poetry_db() -> Path:
    """
    Return path to poetry database.
    Returns None if not available.
    """
    possible_paths = [
        Path(__file__).parent / "poetry.db",
        Path(__file__).parent.parent.parent / "data" / "poetry.db",
        Path.cwd() / "data" / "poetry.db",
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_file():
            return path.resolve()
    
    return None
