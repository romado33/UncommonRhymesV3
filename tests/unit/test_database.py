#!/usr/bin/env python3
"""
Unit Tests for Database Operations
Testing async database manager and operations
"""

import pytest
import asyncio
import tempfile
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rhyme_core.database import AsyncDatabaseManager, DatabaseConfig
from rhyme_core.exceptions import DatabaseError, DatabaseConnectionError

class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_database_config_defaults(self):
        """Test default database configuration"""
        config = DatabaseConfig()
        assert config.path == "data/words_index.sqlite"
        assert config.pool_size == 10
        assert config.timeout == 30.0
        assert config.journal_mode == "WAL"
    
    def test_database_config_custom(self):
        """Test custom database configuration"""
        config = DatabaseConfig(
            path="test.db",
            pool_size=5,
            timeout=10.0
        )
        assert config.path == "test.db"
        assert config.pool_size == 5
        assert config.timeout == 10.0

class TestAsyncDatabaseManager:
    """Test async database manager"""
    
    @pytest.fixture
    async def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create test database with sample data
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Create words table
        cur.execute("""
            CREATE TABLE words (
                word TEXT PRIMARY KEY,
                syls INTEGER,
                stress TEXT,
                pron TEXT,
                k1 TEXT,
                k2 TEXT,
                k3 TEXT,
                zipf REAL
            )
        """)
        
        # Insert test data
        test_data = [
            ("double", 2, "1-0", "D AH1 B AH0 L", "AH", "AH|B AH0 L", "AH1|B AH0 L", 4.5),
            ("trouble", 2, "1-0", "T R AH1 B AH0 L", "AH", "AH|B AH0 L", "AH1|B AH0 L", 4.2),
            ("bubble", 2, "1-0", "B AH1 B AH0 L", "AH", "AH|B AH0 L", "AH1|B AH0 L", 3.8),
            ("table", 2, "1-0", "T EY1 B AH0 L", "AH", "AH|B AH0 L", "AH1|B AH0 L", 4.0),
            ("single", 2, "1-0", "S IH1 NG G AH0 L", "AH", "AH|G AH0 L", "AH1|G AH0 L", 3.5)
        ]
        
        cur.executemany("""
            INSERT INTO words (word, syls, stress, pron, k1, k2, k3, zipf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, test_data)
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_database_manager_initialization(self, temp_db):
        """Test database manager initialization"""
        config = DatabaseConfig(path=temp_db, pool_size=2)
        manager = AsyncDatabaseManager(config)
        
        await manager.initialize()
        assert manager._initialized is True
        assert len(manager._pool) == 2
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_database_manager_connection_pool(self, temp_db):
        """Test connection pool functionality"""
        config = DatabaseConfig(path=temp_db, pool_size=3)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test getting and returning connections
        async with manager.get_connection() as conn:
            assert conn is not None
            # Connection should be returned to pool automatically
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_execute_query(self, temp_db):
        """Test basic query execution"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test simple query
        results = await manager.execute_query("SELECT word FROM words WHERE syls = ?", (2,))
        assert len(results) == 5  # All test words have 2 syllables
        
        # Test query with no results
        results = await manager.execute_query("SELECT word FROM words WHERE syls = ?", (5,))
        assert len(results) == 0
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_execute_query_one(self, temp_db):
        """Test single result query"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test query that returns one result
        result = await manager.execute_query_one("SELECT word FROM words WHERE word = ?", ("double",))
        assert result is not None
        assert result[0] == "double"
        
        # Test query that returns no results
        result = await manager.execute_query_one("SELECT word FROM words WHERE word = ?", ("nonexistent",))
        assert result is None
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_get_phonetic_keys(self, temp_db):
        """Test phonetic keys retrieval"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test existing word
        keys = await manager.get_phonetic_keys("double")
        assert keys is not None
        assert keys == ("AH", "AH|B AH0 L", "AH1|B AH0 L")
        
        # Test non-existing word
        keys = await manager.get_phonetic_keys("nonexistent")
        assert keys is None
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_get_word_data(self, temp_db):
        """Test word data retrieval"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test existing word
        data = await manager.get_word_data("double")
        assert data is not None
        assert data[0] == 2  # syllables
        assert data[1] == "1-0"  # stress
        assert data[2] == "D AH1 B AH0 L"  # pronunciation
        
        # Test non-existing word
        data = await manager.get_word_data("nonexistent")
        assert data is None
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_get_multiword_metrical_data(self, temp_db):
        """Test multi-word metrical data calculation"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Test single word (should work like get_word_data)
        syls, stress, meter = await manager.get_multiword_metrical_data("double")
        assert syls == 2
        assert stress == "1-0"
        assert meter == "trochee"
        
        # Test multi-word phrase
        syls, stress, meter = await manager.get_multiword_metrical_data("double trouble")
        assert syls == 4  # 2 + 2
        assert stress == "1-0-1-0"
        assert meter == "unknown"  # Complex pattern not in METRICAL_FEET
        
        # Test phrase with non-existing words
        syls, stress, meter = await manager.get_multiword_metrical_data("nonexistent word")
        assert syls == 0
        assert stress == ""
        assert meter == "unknown"
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_query_perfect_rhymes(self, temp_db):
        """Test perfect rhyme querying"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Query perfect rhymes for "double" (K3 = "AH1|B AH0 L")
        results = await manager.query_perfect_rhymes("AH1|B AH0 L", "double")
        
        # Should find "trouble" and "bubble" (same K3)
        assert len(results) >= 2
        words = [row[0] for row in results]
        assert "trouble" in words
        assert "bubble" in words
        assert "double" not in words  # Should be excluded
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_query_slant_rhymes(self, temp_db):
        """Test slant rhyme querying"""
        config = DatabaseConfig(path=temp_db, pool_size=1)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Query slant rhymes for "double" (K2 = "AH|B AH0 L", K1 = "AH")
        results = await manager.query_slant_rhymes("AH|B AH0 L", "AH", "double")
        
        # Should find words with matching K2 or K1
        assert len(results) >= 1
        words = [row[0] for row in results]
        assert "double" not in words  # Should be excluded
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error handling"""
        config = DatabaseConfig(path="nonexistent.db", pool_size=1)
        manager = AsyncDatabaseManager(config)
        
        # Should raise FileNotFoundError for non-existent database
        with pytest.raises(FileNotFoundError):
            await manager.initialize()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_db):
        """Test concurrent database operations"""
        config = DatabaseConfig(path=temp_db, pool_size=3)
        manager = AsyncDatabaseManager(config)
        await manager.initialize()
        
        # Run multiple queries concurrently
        tasks = [
            manager.get_phonetic_keys("double"),
            manager.get_phonetic_keys("trouble"),
            manager.get_phonetic_keys("bubble"),
            manager.get_word_data("table"),
            manager.get_word_data("single")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All queries should succeed
        assert all(result is not None for result in results)
        
        await manager.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


