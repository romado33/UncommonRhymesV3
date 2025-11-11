#!/usr/bin/env python3
"""
Custom Exceptions for RhymeRarity
Comprehensive exception hierarchy for better error handling
"""

class RhymeRarityError(Exception):
    """Base exception for all RhymeRarity errors"""
    pass

class DatabaseError(RhymeRarityError):
    """Database-related errors"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    pass

class DatabaseQueryError(DatabaseError):
    """Database query failed"""
    pass

class DatabaseTimeoutError(DatabaseError):
    """Database operation timed out"""
    pass

class DatabaseCorruptionError(DatabaseError):
    """Database corruption detected"""
    pass

class APIError(RhymeRarityError):
    """API-related errors"""
    pass

class RateLimitError(APIError):
    """API rate limit exceeded"""
    pass

class APITimeoutError(APIError):
    """API request timed out"""
    pass

class APIConnectionError(APIError):
    """API connection failed"""
    pass

class APIResponseError(APIError):
    """Invalid API response"""
    pass

class ValidationError(RhymeRarityError):
    """Input validation errors"""
    pass

class PhoneticError(RhymeRarityError):
    """Phonetic analysis errors"""
    pass

class ConfigurationError(RhymeRarityError):
    """Configuration errors"""
    pass

class SearchError(RhymeRarityError):
    """Search operation errors"""
    pass

class CacheError(RhymeRarityError):
    """Caching errors"""
    pass


