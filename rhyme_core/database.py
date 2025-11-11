#!/usr/bin/env python3
"""
Async Database Manager for RhymeRarity
High-performance database operations with connection pooling and async support
"""

import asyncio
import aiosqlite
import sqlite3
import logging
from typing import Dict, List, Tuple, Optional, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger('rhyme_core.database')

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "data/words_index.sqlite"
    pool_size: int = 10
    timeout: float = 30.0
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    cache_size: int = -64000  # 64MB cache
    temp_store: str = "MEMORY"

class AsyncDatabaseManager:
    """
    High-performance async database manager with connection pooling
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: List[aiosqlite.Connection] = []
        self._pool_lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return
        
        logger.info(f"Initializing database pool with {self.config.pool_size} connections")
        
        # Ensure database file exists
        db_path = Path(self.config.path)
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.config.path}")
        
        # Create connection pool
        for _ in range(self.config.pool_size):
            conn = await aiosqlite.connect(
                self.config.path,
                timeout=self.config.timeout
            )
            
            # Optimize connection settings
            await conn.execute(f"PRAGMA journal_mode={self.config.journal_mode}")
            await conn.execute(f"PRAGMA synchronous={self.config.synchronous}")
            await conn.execute(f"PRAGMA cache_size={self.config.cache_size}")
            await conn.execute(f"PRAGMA temp_store={self.config.temp_store}")
            await conn.execute("PRAGMA foreign_keys=ON")
            
            self._pool.append(conn)
        
        self._initialized = True
        logger.info("Database pool initialized successfully")
    
    async def close(self):
        """Close all connections in the pool"""
        async with self._pool_lock:
            for conn in self._pool:
                await conn.close()
            self._pool.clear()
        self._initialized = False
        logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool (context manager)"""
        if not self._initialized:
            await self.initialize()
        
        async with self._pool_lock:
            if not self._pool:
                raise RuntimeError("No connections available in pool")
            conn = self._pool.pop()
        
        try:
            yield conn
        finally:
            async with self._pool_lock:
                self._pool.append(conn)
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """Execute a single query and return results"""
        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchall()
    
    async def execute_query_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """Execute a single query and return one result"""
        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchone()
    
    async def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute a query with multiple parameter sets"""
        async with self.get_connection() as conn:
            await conn.executemany(query, params_list)
            await conn.commit()
    
    async def get_phonetic_keys(self, word: str) -> Optional[Tuple[str, str, str]]:
        """Get K1, K2, K3 phonetic keys for a word"""
        try:
            result = await self.execute_query_one(
                "SELECT k1, k2, k3 FROM words WHERE word = ? LIMIT 1",
                (word.lower(),)
            )
            return result if result else None
        except Exception as e:
            logger.error(f"Error getting phonetic keys for '{word}': {e}")
            return None
    
    async def get_word_data(self, word: str) -> Optional[Tuple[int, str, str]]:
        """Get syllable count, stress pattern, and pronunciation for a word"""
        try:
            result = await self.execute_query_one(
                "SELECT syls, stress, pron FROM words WHERE word = ? LIMIT 1",
                (word.lower(),)
            )
            return result if result else None
        except Exception as e:
            logger.error(f"Error getting word data for '{word}': {e}")
            return None
    
    async def get_multiword_metrical_data(self, phrase: str) -> Tuple[int, str, str]:
        """
        Get metrical data for multi-word phrases by analyzing each word individually.
        
        Args:
            phrase: Multi-word phrase like "hit her" or "on her hand"
            
        Returns:
            tuple: (total_syllables, combined_stress_pattern, metrical_foot_name)
        """
        words = phrase.lower().split()
        if not words:
            return 0, "", "unknown"
        
        try:
            # Batch query for all words in the phrase
            placeholders = ','.join('?' * len(words))
            query = f"SELECT word, syls, stress FROM words WHERE word IN ({placeholders})"
            
            results = await self.execute_query(query, words)
            word_data = {row[0]: (row[1], row[2]) for row in results}
            
            total_syls = 0
            stress_patterns = []
            
            for word in words:
                if word in word_data:
                    syls, stress = word_data[word]
                    total_syls += syls
                    if stress:
                        # Parse stress pattern and add to combined pattern
                        if '-' in stress:
                            stress_list = [int(s) for s in stress.split('-') if s.isdigit()]
                        else:
                            stress_list = [int(s) for s in stress if s.isdigit()]
                        stress_patterns.extend(stress_list)
            
            if total_syls > 0 and stress_patterns:
                # Convert combined stress pattern to metrical foot
                stress_tuple = tuple(stress_patterns)
                
                # Metrical feet mapping
                METRICAL_FEET = {
                    (0, 1): "iamb",
                    (1, 0): "trochee", 
                    (1, 0, 1): "amphibrach",
                    (1, 1, 0): "dactyl",
                    (0, 0, 1): "anapest",
                    (1, 1): "spondee",
                    (0, 0): "pyrrhic"
                }
                
                metrical_foot = METRICAL_FEET.get(stress_tuple, "unknown")
                
                # Format stress pattern for display
                stress_display = '-'.join(map(str, stress_patterns))
                
                return total_syls, stress_display, metrical_foot
            
        except Exception as e:
            logger.error(f"Error getting metrical data for phrase '{phrase}': {e}")
        
        return 0, "", "unknown"
    
    async def query_perfect_rhymes(self, k3: str, exclude_word: str) -> List[Tuple[str, float, str, str, str]]:
        """Query perfect rhymes using K3 key"""
        try:
            results = await self.execute_query(
                "SELECT word, zipf, k1, k2, k3 FROM words WHERE k3 = ? AND word != ? ORDER BY zipf ASC",
                (k3, exclude_word.lower())
            )
            return results
        except Exception as e:
            logger.error(f"Error querying perfect rhymes for k3 '{k3}': {e}")
            return []
    
    async def query_slant_rhymes(self, k2: str, k1: str, exclude_word: str) -> List[Tuple[str, float, str, str, str]]:
        """Query slant rhymes using K2 and K1 keys"""
        try:
            results = await self.execute_query(
                "SELECT word, zipf, k1, k2, k3 FROM words WHERE (k2 = ? OR k1 = ?) AND word != ? ORDER BY zipf ASC",
                (k2, k1, exclude_word.lower())
            )
            return results
        except Exception as e:
            logger.error(f"Error querying slant rhymes for k2 '{k2}', k1 '{k1}': {e}")
            return []

# Global database manager instance
_db_manager: Optional[AsyncDatabaseManager] = None

async def get_database_manager() -> AsyncDatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig()
        _db_manager = AsyncDatabaseManager(config)
        await _db_manager.initialize()
    return _db_manager

async def close_database_manager():
    """Close the global database manager"""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None


