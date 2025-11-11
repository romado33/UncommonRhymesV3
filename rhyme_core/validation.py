#!/usr/bin/env python3
"""
Input Validation for RhymeRarity
Comprehensive validation with detailed error messages
"""

import re
from typing import Union, Tuple, Optional
from .exceptions import ValidationError

class InputValidator:
    """Comprehensive input validation for RhymeRarity"""
    
    # Valid syllable filter options
    VALID_SYLLABLE_FILTERS = ["Any", "1", "2", "3", "4", "5", "5+"]
    
    # Valid stress pattern regex (allows 0, 1, and hyphens)
    STRESS_PATTERN_REGEX = re.compile(r'^[01\-]+$')
    
    # Word validation regex (letters, spaces, hyphens, apostrophes, periods)
    WORD_REGEX = re.compile(r'^[a-z\s\-\.\']+$', re.IGNORECASE)
    
    @staticmethod
    def validate_word(word: Union[str, None]) -> str:
        """
        Validate and normalize a word for rhyme searching.
        
        Args:
            word: Word to validate
            
        Returns:
            Normalized word (lowercase, stripped)
            
        Raises:
            ValidationError: If word is invalid
        """
        if not word:
            raise ValidationError("Word cannot be empty or None")
        
        if not isinstance(word, str):
            raise ValidationError(f"Word must be a string, got {type(word).__name__}")
        
        word = word.strip()
        if not word:
            raise ValidationError("Word cannot be empty after stripping whitespace")
        
        if len(word) > 50:
            raise ValidationError(f"Word too long: {len(word)} characters (max 50)")
        
        if not InputValidator.WORD_REGEX.match(word):
            raise ValidationError(f"Word contains invalid characters: '{word}' (only letters, spaces, hyphens, apostrophes, and periods allowed)")
        
        # Check for excessive punctuation
        if word.count('-') > 3:
            raise ValidationError("Word contains too many hyphens")
        
        if word.count("'") > 2:
            raise ValidationError("Word contains too many apostrophes")
        
        return word.lower()
    
    @staticmethod
    def validate_syllable_filter(syl_filter: Union[str, None]) -> str:
        """
        Validate syllable filter option.
        
        Args:
            syl_filter: Syllable filter to validate
            
        Returns:
            Validated syllable filter
            
        Raises:
            ValidationError: If filter is invalid
        """
        if not syl_filter:
            return "Any"
        
        if not isinstance(syl_filter, str):
            raise ValidationError(f"Syllable filter must be a string, got {type(syl_filter).__name__}")
        
        syl_filter = syl_filter.strip()
        if syl_filter not in InputValidator.VALID_SYLLABLE_FILTERS:
            valid_options = ", ".join(InputValidator.VALID_SYLLABLE_FILTERS)
            raise ValidationError(f"Invalid syllable filter: '{syl_filter}'. Valid options: {valid_options}")
        
        return syl_filter
    
    @staticmethod
    def validate_stress_filter(stress_filter: Union[str, None]) -> str:
        """
        Validate stress pattern filter.
        
        Args:
            stress_filter: Stress pattern to validate
            
        Returns:
            Validated stress pattern
            
        Raises:
            ValidationError: If pattern is invalid
        """
        if not stress_filter or stress_filter.strip() == "Any":
            return "Any"
        
        if not isinstance(stress_filter, str):
            raise ValidationError(f"Stress filter must be a string, got {type(stress_filter).__name__}")
        
        stress_filter = stress_filter.strip()
        if not stress_filter:
            return "Any"
        
        if not InputValidator.STRESS_PATTERN_REGEX.match(stress_filter):
            raise ValidationError(f"Invalid stress pattern: '{stress_filter}'. Must contain only 0, 1, and hyphens (e.g., '1-0-1')")
        
        # Validate pattern structure
        if stress_filter.startswith('-') or stress_filter.endswith('-'):
            raise ValidationError("Stress pattern cannot start or end with a hyphen")
        
        if '--' in stress_filter:
            raise ValidationError("Stress pattern cannot contain consecutive hyphens")
        
        # Check for reasonable length
        if len(stress_filter) > 20:
            raise ValidationError("Stress pattern too long (max 20 characters)")
        
        return stress_filter
    
    @staticmethod
    def validate_boolean_flag(flag: Union[bool, str, None], name: str) -> bool:
        """
        Validate boolean flag parameters.
        
        Args:
            flag: Boolean flag to validate
            name: Name of the parameter for error messages
            
        Returns:
            Boolean value
            
        Raises:
            ValidationError: If flag is invalid
        """
        if flag is None:
            return False
        
        if isinstance(flag, bool):
            return flag
        
        if isinstance(flag, str):
            flag_lower = flag.lower().strip()
            if flag_lower in ('true', '1', 'yes', 'on', 'enabled'):
                return True
            elif flag_lower in ('false', '0', 'no', 'off', 'disabled'):
                return False
            else:
                raise ValidationError(f"Invalid {name} value: '{flag}'. Must be true/false, 1/0, yes/no, on/off, or enabled/disabled")
        
        raise ValidationError(f"{name} must be a boolean or string, got {type(flag).__name__}")
    
    @staticmethod
    def validate_search_parameters(
        target_word: Union[str, None],
        syl_filter: Union[str, None] = None,
        stress_filter: Union[str, None] = None,
        use_datamuse: Union[bool, str, None] = None,
        multisyl_only: Union[bool, str, None] = None,
        enable_alliteration: Union[bool, str, None] = None
    ) -> Tuple[str, str, str, bool, bool, bool]:
        """
        Validate all search parameters at once.
        
        Args:
            target_word: Word to search for
            syl_filter: Syllable count filter
            stress_filter: Stress pattern filter
            use_datamuse: Enable Datamuse API
            multisyl_only: Only multi-syllable results
            enable_alliteration: Enable alliteration bonus
            
        Returns:
            Tuple of validated parameters
            
        Raises:
            ValidationError: If any parameter is invalid
        """
        try:
            validated_word = InputValidator.validate_word(target_word)
            validated_syl = InputValidator.validate_syllable_filter(syl_filter)
            validated_stress = InputValidator.validate_stress_filter(stress_filter)
            validated_datamuse = InputValidator.validate_boolean_flag(use_datamuse, "use_datamuse")
            validated_multisyl = InputValidator.validate_boolean_flag(multisyl_only, "multisyl_only")
            validated_alliteration = InputValidator.validate_boolean_flag(enable_alliteration, "enable_alliteration")
            
            return (
                validated_word,
                validated_syl,
                validated_stress,
                validated_datamuse,
                validated_multisyl,
                validated_alliteration
            )
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected validation error: {e}")
    
    @staticmethod
    def validate_configuration(config_dict: dict) -> dict:
        """
        Validate configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary to validate
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValidationError: If configuration is invalid
        """
        if not isinstance(config_dict, dict):
            raise ValidationError("Configuration must be a dictionary")
        
        validated_config = {}
        
        # Validate database configuration
        if 'database' in config_dict:
            db_config = config_dict['database']
            if not isinstance(db_config, dict):
                raise ValidationError("Database configuration must be a dictionary")
            
            # Validate database path
            if 'path' in db_config:
                if not isinstance(db_config['path'], str):
                    raise ValidationError("Database path must be a string")
                if not db_config['path'].strip():
                    raise ValidationError("Database path cannot be empty")
            
            # Validate pool size
            if 'pool_size' in db_config:
                pool_size = db_config['pool_size']
                if not isinstance(pool_size, int):
                    raise ValidationError("Database pool size must be an integer")
                if pool_size < 1 or pool_size > 100:
                    raise ValidationError("Database pool size must be between 1 and 100")
            
            validated_config['database'] = db_config
        
        # Validate API configuration
        if 'api' in config_dict:
            api_config = config_dict['api']
            if not isinstance(api_config, dict):
                raise ValidationError("API configuration must be a dictionary")
            
            # Validate timeout
            if 'timeout' in api_config:
                timeout = api_config['timeout']
                if not isinstance(timeout, (int, float)):
                    raise ValidationError("API timeout must be a number")
                if timeout < 0.1 or timeout > 30.0:
                    raise ValidationError("API timeout must be between 0.1 and 30.0 seconds")
            
            validated_config['api'] = api_config
        
        # Validate search configuration
        if 'search' in config_dict:
            search_config = config_dict['search']
            if not isinstance(search_config, dict):
                raise ValidationError("Search configuration must be a dictionary")
            
            # Validate score ranges
            for score_field in ['min_score']:
                if score_field in search_config:
                    score = search_config[score_field]
                    if not isinstance(score, (int, float)):
                        raise ValidationError(f"{score_field} must be a number")
                    if score < 0.0 or score > 1.0:
                        raise ValidationError(f"{score_field} must be between 0.0 and 1.0")
            
            # Validate limits
            for limit_field in ['max_items', 'max_perfect_popular', 'max_perfect_technical']:
                if limit_field in search_config:
                    limit = search_config[limit_field]
                    if not isinstance(limit, int):
                        raise ValidationError(f"{limit_field} must be an integer")
                    if limit < 1 or limit > 10000:
                        raise ValidationError(f"{limit_field} must be between 1 and 10000")
            
            validated_config['search'] = search_config
        
        return validated_config


