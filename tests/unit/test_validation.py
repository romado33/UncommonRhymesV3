#!/usr/bin/env python3
"""
Unit Tests for Input Validation
Comprehensive testing of validation functions
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rhyme_core.validation import InputValidator
from rhyme_core.exceptions import ValidationError

class TestWordValidation:
    """Test word validation functionality"""
    
    def test_validate_word_basic(self):
        """Test basic word validation"""
        result = InputValidator.validate_word("double")
        assert result == "double"
    
    def test_validate_word_case_normalization(self):
        """Test case normalization"""
        result = InputValidator.validate_word("DOUBLE")
        assert result == "double"
    
    def test_validate_word_whitespace_trimming(self):
        """Test whitespace trimming"""
        result = InputValidator.validate_word("  double  ")
        assert result == "double"
    
    def test_validate_word_with_hyphen(self):
        """Test word with hyphen"""
        result = InputValidator.validate_word("double-check")
        assert result == "double-check"
    
    def test_validate_word_with_apostrophe(self):
        """Test word with apostrophe"""
        result = InputValidator.validate_word("don't")
        assert result == "don't"
    
    def test_validate_word_empty(self):
        """Test empty word validation"""
        with pytest.raises(ValidationError, match="Word cannot be empty"):
            InputValidator.validate_word("")
    
    def test_validate_word_none(self):
        """Test None word validation"""
        with pytest.raises(ValidationError, match="Word cannot be empty or None"):
            InputValidator.validate_word(None)
    
    def test_validate_word_too_long(self):
        """Test word that's too long"""
        long_word = "a" * 51
        with pytest.raises(ValidationError, match="Word too long"):
            InputValidator.validate_word(long_word)
    
    def test_validate_word_invalid_characters(self):
        """Test word with invalid characters"""
        with pytest.raises(ValidationError, match="Word contains invalid characters"):
            InputValidator.validate_word("double123")
    
    def test_validate_word_too_many_hyphens(self):
        """Test word with too many hyphens"""
        with pytest.raises(ValidationError, match="too many hyphens"):
            InputValidator.validate_word("double-check-test-more")
    
    def test_validate_word_too_many_apostrophes(self):
        """Test word with too many apostrophes"""
        with pytest.raises(ValidationError, match="too many apostrophes"):
            InputValidator.validate_word("don't't")

class TestSyllableFilterValidation:
    """Test syllable filter validation"""
    
    def test_validate_syllable_filter_valid(self):
        """Test valid syllable filters"""
        valid_filters = ["Any", "1", "2", "3", "4", "5", "5+"]
        for filter_val in valid_filters:
            result = InputValidator.validate_syllable_filter(filter_val)
            assert result == filter_val
    
    def test_validate_syllable_filter_case_sensitive(self):
        """Test that syllable filters are case sensitive"""
        with pytest.raises(ValidationError, match="Invalid syllable filter"):
            InputValidator.validate_syllable_filter("any")
    
    def test_validate_syllable_filter_invalid(self):
        """Test invalid syllable filter"""
        with pytest.raises(ValidationError, match="Invalid syllable filter"):
            InputValidator.validate_syllable_filter("6")
    
    def test_validate_syllable_filter_none(self):
        """Test None syllable filter"""
        result = InputValidator.validate_syllable_filter(None)
        assert result == "Any"
    
    def test_validate_syllable_filter_whitespace(self):
        """Test syllable filter with whitespace"""
        result = InputValidator.validate_syllable_filter("  2  ")
        assert result == "2"

class TestStressFilterValidation:
    """Test stress filter validation"""
    
    def test_validate_stress_filter_any(self):
        """Test 'Any' stress filter"""
        result = InputValidator.validate_stress_filter("Any")
        assert result == "Any"
    
    def test_validate_stress_filter_none(self):
        """Test None stress filter"""
        result = InputValidator.validate_stress_filter(None)
        assert result == "Any"
    
    def test_validate_stress_filter_valid_patterns(self):
        """Test valid stress patterns"""
        valid_patterns = ["1-0", "0-1", "1-0-1", "0-0-1", "1-1-0"]
        for pattern in valid_patterns:
            result = InputValidator.validate_stress_filter(pattern)
            assert result == pattern
    
    def test_validate_stress_filter_invalid_characters(self):
        """Test stress pattern with invalid characters"""
        with pytest.raises(ValidationError, match="Invalid stress pattern"):
            InputValidator.validate_stress_filter("1-2-0")
    
    def test_validate_stress_filter_starts_with_hyphen(self):
        """Test stress pattern starting with hyphen"""
        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            InputValidator.validate_stress_filter("-1-0")
    
    def test_validate_stress_filter_ends_with_hyphen(self):
        """Test stress pattern ending with hyphen"""
        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            InputValidator.validate_stress_filter("1-0-")
    
    def test_validate_stress_filter_consecutive_hyphens(self):
        """Test stress pattern with consecutive hyphens"""
        with pytest.raises(ValidationError, match="cannot contain consecutive hyphens"):
            InputValidator.validate_stress_filter("1--0")
    
    def test_validate_stress_filter_too_long(self):
        """Test stress pattern that's too long"""
        long_pattern = "1-0-1-0-1-0-1-0-1-0-1"
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_stress_filter(long_pattern)

class TestBooleanFlagValidation:
    """Test boolean flag validation"""
    
    def test_validate_boolean_flag_true_values(self):
        """Test boolean flag with true values"""
        true_values = [True, "true", "1", "yes", "on", "enabled"]
        for value in true_values:
            result = InputValidator.validate_boolean_flag(value, "test_flag")
            assert result is True
    
    def test_validate_boolean_flag_false_values(self):
        """Test boolean flag with false values"""
        false_values = [False, "false", "0", "no", "off", "disabled"]
        for value in false_values:
            result = InputValidator.validate_boolean_flag(value, "test_flag")
            assert result is False
    
    def test_validate_boolean_flag_none(self):
        """Test boolean flag with None"""
        result = InputValidator.validate_boolean_flag(None, "test_flag")
        assert result is False
    
    def test_validate_boolean_flag_invalid(self):
        """Test boolean flag with invalid value"""
        with pytest.raises(ValidationError, match="Invalid test_flag value"):
            InputValidator.validate_boolean_flag("maybe", "test_flag")
    
    def test_validate_boolean_flag_wrong_type(self):
        """Test boolean flag with wrong type"""
        with pytest.raises(ValidationError, match="must be a boolean or string"):
            InputValidator.validate_boolean_flag(123, "test_flag")

class TestSearchParametersValidation:
    """Test comprehensive search parameter validation"""
    
    def test_validate_search_parameters_valid(self):
        """Test valid search parameters"""
        result = InputValidator.validate_search_parameters(
            target_word="double",
            syl_filter="2",
            stress_filter="1-0",
            use_datamuse=True,
            multisyl_only=False,
            enable_alliteration=True
        )
        
        expected = ("double", "2", "1-0", True, False, True)
        assert result == expected
    
    def test_validate_search_parameters_minimal(self):
        """Test minimal search parameters"""
        result = InputValidator.validate_search_parameters("double")
        
        expected = ("double", "Any", "Any", False, False, False)
        assert result == expected
    
    def test_validate_search_parameters_invalid_word(self):
        """Test search parameters with invalid word"""
        with pytest.raises(ValidationError, match="Word cannot be empty"):
            InputValidator.validate_search_parameters("")
    
    def test_validate_search_parameters_invalid_syllable_filter(self):
        """Test search parameters with invalid syllable filter"""
        with pytest.raises(ValidationError, match="Invalid syllable filter"):
            InputValidator.validate_search_parameters(
                target_word="double",
                syl_filter="invalid"
            )
    
    def test_validate_search_parameters_invalid_stress_filter(self):
        """Test search parameters with invalid stress filter"""
        with pytest.raises(ValidationError, match="Invalid stress pattern"):
            InputValidator.validate_search_parameters(
                target_word="double",
                stress_filter="1-2-0"
            )

class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_validate_configuration_valid(self):
        """Test valid configuration"""
        config = {
            'database': {
                'path': 'data/test.db',
                'pool_size': 5
            },
            'api': {
                'timeout': 3.0
            },
            'search': {
                'min_score': 0.5,
                'max_items': 100
            }
        }
        
        result = InputValidator.validate_configuration(config)
        assert result == config
    
    def test_validate_configuration_invalid_type(self):
        """Test configuration with invalid type"""
        with pytest.raises(ValidationError, match="Configuration must be a dictionary"):
            InputValidator.validate_configuration("not a dict")
    
    def test_validate_configuration_invalid_database_path(self):
        """Test configuration with invalid database path"""
        config = {
            'database': {
                'path': ''  # Empty path
            }
        }
        
        with pytest.raises(ValidationError, match="Database path cannot be empty"):
            InputValidator.validate_configuration(config)
    
    def test_validate_configuration_invalid_pool_size(self):
        """Test configuration with invalid pool size"""
        config = {
            'database': {
                'pool_size': 0  # Invalid pool size
            }
        }
        
        with pytest.raises(ValidationError, match="Database pool size must be between 1 and 100"):
            InputValidator.validate_configuration(config)
    
    def test_validate_configuration_invalid_timeout(self):
        """Test configuration with invalid timeout"""
        config = {
            'api': {
                'timeout': -1.0  # Invalid timeout
            }
        }
        
        with pytest.raises(ValidationError, match="API timeout must be between 0.1 and 30.0 seconds"):
            InputValidator.validate_configuration(config)
    
    def test_validate_configuration_invalid_score(self):
        """Test configuration with invalid score"""
        config = {
            'search': {
                'min_score': 1.5  # Invalid score
            }
        }
        
        with pytest.raises(ValidationError, match="min_score must be between 0.0 and 1.0"):
            InputValidator.validate_configuration(config)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


