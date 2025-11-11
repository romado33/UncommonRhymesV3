#!/usr/bin/env python3
"""
Async API Client for RhymeRarity
High-performance async HTTP client with retry logic and error handling
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
from urllib.parse import urlencode

logger = logging.getLogger('rhyme_core.api_client')

@dataclass
class APIConfig:
    """API configuration settings"""
    timeout: float = 3.0
    max_retries: int = 3
    backoff_factor: float = 1.0
    rate_limit_delay: float = 2.0
    max_concurrent_requests: int = 10
    user_agent: str = "RhymeRarity/1.0"

class APIError(Exception):
    """Base exception for API errors"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass

class TimeoutError(APIError):
    """Request timeout"""
    pass

class ConnectionError(APIError):
    """Connection error"""
    pass

class AsyncAPIClient:
    """
    High-performance async HTTP client with retry logic and error handling
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_time = 0.0
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self):
        """Initialize the HTTP session"""
        if self._session is not None:
            return
        
        # Create session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.config.user_agent}
        )
        
        logger.info("API client initialized")
    
    async def close(self):
        """Close the HTTP session"""
        if self._session is not None:
            await self._session.close()
            self._session = None
        logger.info("API client closed")
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        async with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < 0.1:  # Minimum 100ms between requests
                await asyncio.sleep(0.1 - time_since_last)
            
            self._last_request_time = time.time()
    
    async def _make_request_with_retry(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        if self._session is None:
            await self.initialize()
        
        # Apply rate limiting
        await self._rate_limit()
        
        # Prepare request
        request_params = params or {}
        full_url = f"{url}?{urlencode(request_params)}" if request_params else url
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._semaphore:
                    async with self._session.get(full_url) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limited
                            logger.warning(f"Rate limited by API (attempt {attempt + 1})")
                            if attempt < self.config.max_retries:
                                delay = self.config.rate_limit_delay * (2 ** attempt)
                                await asyncio.sleep(delay)
                                continue
                            raise RateLimitError(f"Rate limited after {self.config.max_retries} retries")
                        else:
                            response.raise_for_status()
                            
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"Request timeout after {self.config.timeout}s")
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                
            except aiohttp.ClientConnectorError as e:
                last_exception = ConnectionError(f"Connection error: {e}")
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                
            except aiohttp.ClientError as e:
                last_exception = APIError(f"Client error: {e}")
                logger.warning(f"Client error (attempt {attempt + 1}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries:
                delay = self.config.backoff_factor * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(f"All retry attempts failed for URL: {full_url}")
        raise last_exception or APIError("Unknown error occurred")
    
    async def get_datamuse_perfect(self, word: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """Get perfect rhymes from Datamuse API"""
        try:
            params = {
                'rel_rhy': word,
                'max': max_results,
                'md': 'fp'  # f=frequency, p=pronunciation
            }
            
            results = await self._make_request_with_retry(
                'https://api.datamuse.com/words',
                params
            )
            
            return self._parse_datamuse_response(results, 'perfect')
            
        except Exception as e:
            logger.error(f"Error fetching Datamuse perfect rhymes for '{word}': {e}")
            return []
    
    async def get_datamuse_near(self, word: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """Get near rhymes from Datamuse API"""
        try:
            params = {
                'rel_nry': word,
                'max': max_results,
                'md': 'fp'
            }
            
            results = await self._make_request_with_retry(
                'https://api.datamuse.com/words',
                params
            )
            
            return self._parse_datamuse_response(results, 'near')
            
        except Exception as e:
            logger.error(f"Error fetching Datamuse near rhymes for '{word}': {e}")
            return []
    
    async def get_datamuse_approximate(self, word: str, max_results: int = 500) -> List[Dict[str, Any]]:
        """Get approximate rhymes from Datamuse API"""
        try:
            params = {
                'rel_app': word,
                'max': max_results,
                'md': 'fp'
            }
            
            results = await self._make_request_with_retry(
                'https://api.datamuse.com/words',
                params
            )
            
            return self._parse_datamuse_response(results, 'approximate')
            
        except Exception as e:
            logger.error(f"Error fetching Datamuse approximate rhymes for '{word}': {e}")
            return []
    
    async def get_datamuse_comprehensive(self, word: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive results from all Datamuse endpoints concurrently"""
        try:
            # Create tasks for concurrent execution
            tasks = [
                self.get_datamuse_perfect(word, 1000),
                self.get_datamuse_near(word, 1000),
                self.get_datamuse_approximate(word, 500)
            ]
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            perfect_results = results[0] if not isinstance(results[0], Exception) else []
            near_results = results[1] if not isinstance(results[1], Exception) else []
            approximate_results = results[2] if not isinstance(results[2], Exception) else []
            
            return {
                'perfect': perfect_results,
                'near': near_results,
                'approximate': approximate_results
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive Datamuse fetch for '{word}': {e}")
            return {'perfect': [], 'near': [], 'approximate': []}
    
    def _parse_datamuse_response(self, results: List[Dict], rhyme_type: str) -> List[Dict[str, Any]]:
        """Parse Datamuse API response format"""
        parsed_results = []
        
        for item in results:
            word_text = item.get('word', '')
            tags = item.get('tags', [])
            score = item.get('score', 0)
            
            # Extract frequency and pronunciation from tags
            freq_score = self._extract_frequency_from_tags(tags)
            pron = self._extract_pronunciation_from_tags(tags)
            
            parsed_results.append({
                'word': word_text,
                'score': score,
                'freq': freq_score,
                'pron': pron,
                'tags': tags,
                'is_multiword': ' ' in word_text,
                'datamuse_verified': True,
                'rhyme_type': rhyme_type
            })
        
        return parsed_results
    
    def _extract_frequency_from_tags(self, tags: List[str]) -> float:
        """Extract frequency score from Datamuse tags"""
        for tag in tags:
            if tag.startswith('f:'):
                try:
                    return float(tag[2:])
                except ValueError:
                    continue
        return 0.0
    
    def _extract_pronunciation_from_tags(self, tags: List[str]) -> str:
        """Extract pronunciation from Datamuse tags"""
        for tag in tags:
            if tag.startswith('p:'):
                return tag[2:]
        return ""

# Global API client instance
_api_client: Optional[AsyncAPIClient] = None

async def get_api_client() -> AsyncAPIClient:
    """Get the global API client instance"""
    global _api_client
    if _api_client is None:
        config = APIConfig()
        _api_client = AsyncAPIClient(config)
        await _api_client.initialize()
    return _api_client

async def close_api_client():
    """Close the global API client"""
    global _api_client
    if _api_client is not None:
        await _api_client.close()
        _api_client = None


