#!/usr/bin/env python3
"""
Comprehensive Error Handling for RhymeRarity
Centralized error handling with logging and graceful degradation
"""

import logging
import traceback
import functools
from typing import Any, Callable, Optional, Dict, List
from contextlib import contextmanager
import time

from .exceptions import (
    RhymeRarityError, DatabaseError, APIError, ValidationError,
    DatabaseConnectionError, DatabaseQueryError, DatabaseTimeoutError,
    RateLimitError, APITimeoutError, APIConnectionError
)

logger = logging.getLogger('rhyme_core.error_handler')

class ErrorHandler:
    """Centralized error handling with comprehensive logging and recovery"""
    
    def __init__(self, enable_graceful_degradation: bool = True):
        self.enable_graceful_degradation = enable_graceful_degradation
        self.error_counts: Dict[str, int] = {}
        self.last_error_times: Dict[str, float] = {}
    
    def handle_database_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> Any:
        """Handle database-related errors with appropriate recovery"""
        error_type = type(error).__name__
        error_key = f"db_{error_type}_{operation}"
        
        # Log the error
        logger.error(f"Database error in {operation}: {error}")
        if context:
            logger.error(f"Context: {context}")
        
        # Track error frequency
        self._track_error(error_key)
        
        # Determine recovery strategy
        if isinstance(error, sqlite3.OperationalError):
            if "database is locked" in str(error).lower():
                logger.warning("Database locked, retrying after delay")
                time.sleep(0.1)
                return None  # Signal retry
            elif "no such table" in str(error).lower():
                raise DatabaseError(f"Database schema error: {error}")
            else:
                raise DatabaseConnectionError(f"Database operational error: {error}")
        
        elif isinstance(error, sqlite3.DatabaseError):
            raise DatabaseCorruptionError(f"Database corruption detected: {error}")
        
        elif isinstance(error, sqlite3.TimeoutError):
            raise DatabaseTimeoutError(f"Database operation timed out: {error}")
        
        else:
            raise DatabaseError(f"Unexpected database error: {error}")
    
    def handle_api_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> Any:
        """Handle API-related errors with appropriate recovery"""
        error_type = type(error).__name__
        error_key = f"api_{error_type}_{operation}"
        
        # Log the error
        logger.error(f"API error in {operation}: {error}")
        if context:
            logger.error(f"Context: {context}")
        
        # Track error frequency
        self._track_error(error_key)
        
        # Determine recovery strategy
        if isinstance(error, requests.exceptions.Timeout):
            logger.warning("API request timed out")
            if self.enable_graceful_degradation:
                return []  # Return empty results
            raise APITimeoutError(f"API request timed out: {error}")
        
        elif isinstance(error, requests.exceptions.ConnectionError):
            logger.warning("API connection failed")
            if self.enable_graceful_degradation:
                return []  # Return empty results
            raise APIConnectionError(f"API connection failed: {error}")
        
        elif isinstance(error, requests.exceptions.HTTPError):
            if error.response.status_code == 429:
                logger.warning("API rate limit exceeded")
                if self.enable_graceful_degradation:
                    time.sleep(2)  # Wait before retry
                    return []  # Return empty results for now
                raise RateLimitError(f"API rate limit exceeded: {error}")
            else:
                logger.error(f"API HTTP error: {error.response.status_code}")
                if self.enable_graceful_degradation:
                    return []
                raise APIError(f"API HTTP error: {error}")
        
        else:
            if self.enable_graceful_degradation:
                return []
            raise APIError(f"Unexpected API error: {error}")
    
    def handle_validation_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> Any:
        """Handle validation errors"""
        error_type = type(error).__name__
        error_key = f"validation_{error_type}_{operation}"
        
        # Log the error
        logger.error(f"Validation error in {operation}: {error}")
        if context:
            logger.error(f"Context: {context}")
        
        # Track error frequency
        self._track_error(error_key)
        
        # Validation errors should always be raised (no graceful degradation)
        raise ValidationError(f"Input validation failed: {error}")
    
    def handle_general_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> Any:
        """Handle general errors with logging and recovery"""
        error_type = type(error).__name__
        error_key = f"general_{error_type}_{operation}"
        
        # Log the error with full traceback
        logger.error(f"Unexpected error in {operation}: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if context:
            logger.error(f"Context: {context}")
        
        # Track error frequency
        self._track_error(error_key)
        
        # For unexpected errors, use graceful degradation if enabled
        if self.enable_graceful_degradation:
            logger.warning(f"Graceful degradation enabled, returning empty result for {operation}")
            return [] if isinstance(error, (list, tuple)) else None
        
        raise RhymeRarityError(f"Unexpected error in {operation}: {error}")
    
    def _track_error(self, error_key: str):
        """Track error frequency for monitoring"""
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_error_times[error_key] = time.time()
        
        # Log warning if error frequency is high
        if self.error_counts[error_key] > 10:
            logger.warning(f"High error frequency for {error_key}: {self.error_counts[error_key]} errors")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': self.error_counts.copy(),
            'last_error_times': self.last_error_times.copy(),
            'total_errors': sum(self.error_counts.values())
        }
    
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_counts.clear()
        self.last_error_times.clear()

# Global error handler instance
_error_handler = ErrorHandler()

def handle_errors(operation: str, error_type: str = "general"):
    """
    Decorator for comprehensive error handling
    
    Args:
        operation: Name of the operation for logging
        error_type: Type of error handling ("database", "api", "validation", "general")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                return _error_handler.handle_validation_error(e, operation, {'args': args, 'kwargs': kwargs})
            except (DatabaseError, sqlite3.Error) as e:
                return _error_handler.handle_database_error(e, operation, {'args': args, 'kwargs': kwargs})
            except (APIError, requests.exceptions.RequestException) as e:
                return _error_handler.handle_api_error(e, operation, {'args': args, 'kwargs': kwargs})
            except Exception as e:
                return _error_handler.handle_general_error(e, operation, {'args': args, 'kwargs': kwargs})
        return wrapper
    return decorator

@contextmanager
def error_context(operation: str, error_type: str = "general"):
    """
    Context manager for error handling
    
    Args:
        operation: Name of the operation for logging
        error_type: Type of error handling
    """
    try:
        yield
    except ValidationError as e:
        _error_handler.handle_validation_error(e, operation)
    except (DatabaseError, sqlite3.Error) as e:
        _error_handler.handle_database_error(e, operation)
    except (APIError, requests.exceptions.RequestException) as e:
        _error_handler.handle_api_error(e, operation)
    except Exception as e:
        _error_handler.handle_general_error(e, operation)

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _error_handler

def configure_error_handling(enable_graceful_degradation: bool = True):
    """Configure global error handling settings"""
    global _error_handler
    _error_handler = ErrorHandler(enable_graceful_degradation)
    logger.info(f"Error handling configured: graceful_degradation={enable_graceful_degradation}")

# Import required modules for error handling
import sqlite3
import requests


