#!/usr/bin/env python3
"""
Configuration Management for RhymeRarity
JSON-based configuration system with validation and defaults
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger('rhyme_core.config')

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

@dataclass
class APIConfig:
    """API configuration settings"""
    timeout: float = 3.0
    max_retries: int = 3
    backoff_factor: float = 1.0
    rate_limit_delay: float = 2.0
    max_concurrent_requests: int = 10
    user_agent: str = "RhymeRarity/1.0"

@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    enable_caching: bool = True
    cache_size: int = 1000
    enable_connection_pooling: bool = True
    enable_concurrent_requests: bool = True
    enable_async_operations: bool = True

@dataclass
class SearchConfig:
    """Search behavior configuration"""
    # Perfect rhyme settings
    zipf_min_perfect: float = 0.0
    zipf_max_perfect: float = 6.0
    max_perfect_popular: int = 20
    max_perfect_technical: int = 30
    
    # Slant rhyme settings
    zipf_min_slant: float = 0.0
    zipf_max_slant: float = 6.0
    max_slant_near: int = 50
    max_slant_assonance: int = 40
    
    # Multi-word settings
    max_colloquial: int = 15
    
    # General settings
    max_items: int = 200
    min_score: float = 0.35
    enable_alliteration_bonus: bool = True
    enable_multisyl_bonus: bool = True

@dataclass
class LLMConfig:
    """LLM feature configuration"""
    llm_spellfix: bool = False
    llm_query_normalizer: bool = False
    llm_ranker: bool = False
    llm_explanations: bool = False
    llm_multiword_synth: bool = False

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_file: str = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

@dataclass
class PrecisionConfig:
    """Main configuration class combining all settings"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Legacy compatibility fields (for backward compatibility)
    db_path: str = field(init=False)
    zipf_min_perfect: float = field(init=False)
    zipf_max_perfect: float = field(init=False)
    max_perfect_popular: int = field(init=False)
    max_perfect_technical: int = field(init=False)
    zipf_min_slant: float = field(init=False)
    zipf_max_slant: float = field(init=False)
    max_slant_near: int = field(init=False)
    max_slant_assonance: int = field(init=False)
    max_colloquial: int = field(init=False)
    max_items: int = field(init=False)
    min_score: float = field(init=False)
    enable_alliteration_bonus: bool = field(init=False)
    enable_multisyl_bonus: bool = field(init=False)
    
    def __post_init__(self):
        """Initialize legacy compatibility fields"""
        self.db_path = self.database.path
        self.zipf_min_perfect = self.search.zipf_min_perfect
        self.zipf_max_perfect = self.search.zipf_max_perfect
        self.max_perfect_popular = self.search.max_perfect_popular
        self.max_perfect_technical = self.search.max_perfect_technical
        self.zipf_min_slant = self.search.zipf_min_slant
        self.zipf_max_slant = self.search.zipf_max_slant
        self.max_slant_near = self.search.max_slant_near
        self.max_slant_assonance = self.search.max_slant_assonance
        self.max_colloquial = self.search.max_colloquial
        self.max_items = self.search.max_items
        self.min_score = self.search.min_score
        self.enable_alliteration_bonus = self.search.enable_alliteration_bonus
        self.enable_multisyl_bonus = self.search.enable_multisyl_bonus
    
    @classmethod
    def from_file(cls, config_path: str) -> 'PrecisionConfig':
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle nested configuration structure
            config = cls()
            
            # Update nested configs if they exist in the file
            if 'database' in data:
                config.database = DatabaseConfig(**data['database'])
            if 'api' in data:
                config.api = APIConfig(**data['api'])
            if 'performance' in data:
                config.performance = PerformanceConfig(**data['performance'])
            if 'search' in data:
                config.search = SearchConfig(**data['search'])
            if 'llm' in data:
                config.llm = LLMConfig(**data['llm'])
            if 'logging' in data:
                config.logging = LoggingConfig(**data['logging'])
            
            # Handle legacy flat structure for backward compatibility
            legacy_fields = [
                'db_path', 'zipf_min_perfect', 'zipf_max_perfect',
                'max_perfect_popular', 'max_perfect_technical',
                'zipf_min_slant', 'zipf_max_slant', 'max_slant_near',
                'max_slant_assonance', 'max_colloquial', 'max_items',
                'min_score', 'enable_alliteration_bonus', 'enable_multisyl_bonus'
            ]
            
            for field in legacy_fields:
                if field in data:
                    if field == 'db_path':
                        config.database.path = data[field]
                    elif field.startswith('zipf_'):
                        if 'perfect' in field:
                            if 'min' in field:
                                config.search.zipf_min_perfect = data[field]
                            else:
                                config.search.zipf_max_perfect = data[field]
                        else:
                            if 'min' in field:
                                config.search.zipf_min_slant = data[field]
                            else:
                                config.search.zipf_max_slant = data[field]
                    elif field.startswith('max_'):
                        if 'perfect' in field:
                            if 'popular' in field:
                                config.search.max_perfect_popular = data[field]
                            else:
                                config.search.max_perfect_technical = data[field]
                        elif 'slant' in field:
                            if 'near' in field:
                                config.search.max_slant_near = data[field]
                            else:
                                config.search.max_slant_assonance = data[field]
                        elif field == 'max_colloquial':
                            config.search.max_colloquial = data[field]
                        elif field == 'max_items':
                            config.search.max_items = data[field]
                    elif field == 'min_score':
                        config.search.min_score = data[field]
                    elif field.startswith('enable_'):
                        if 'alliteration' in field:
                            config.search.enable_alliteration_bonus = data[field]
                        else:
                            config.search.enable_multisyl_bonus = data[field]
            
            # Re-initialize legacy fields
            config.__post_init__()
            
            logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary
            config_dict = asdict(self)
            
            # Remove legacy fields from the dict (they're computed)
            legacy_fields = [
                'db_path', 'zipf_min_perfect', 'zipf_max_perfect',
                'max_perfect_popular', 'max_perfect_technical',
                'zipf_min_slant', 'zipf_max_slant', 'max_slant_near',
                'max_slant_assonance', 'max_colloquial', 'max_items',
                'min_score', 'enable_alliteration_bonus', 'enable_multisyl_bonus'
            ]
            
            for field in legacy_fields:
                config_dict.pop(field, None)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {e}")
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Validate database path
        if not Path(self.database.path).exists():
            errors.append(f"Database file not found: {self.database.path}")
        
        # Validate numeric ranges
        if self.database.pool_size < 1 or self.database.pool_size > 100:
            errors.append("Database pool size must be between 1 and 100")
        
        if self.api.timeout < 0.1 or self.api.timeout > 30.0:
            errors.append("API timeout must be between 0.1 and 30.0 seconds")
        
        if self.search.min_score < 0.0 or self.search.min_score > 1.0:
            errors.append("Minimum score must be between 0.0 and 1.0")
        
        # Validate search limits
        if self.search.max_items < 1 or self.search.max_items > 10000:
            errors.append("Max items must be between 1 and 10000")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def get_optimized_for_web_service(self) -> 'PrecisionConfig':
        """Get configuration optimized for web service deployment"""
        config = PrecisionConfig()
        
        # Optimize for web service
        config.database.pool_size = 20
        config.database.cache_size = -128000  # 128MB cache
        config.api.max_concurrent_requests = 50
        config.performance.enable_caching = True
        config.performance.cache_size = 5000
        config.search.max_items = 500
        
        return config

# Default configuration instance
default_config = PrecisionConfig()

# Configuration presets
PRESETS = {
    'development': PrecisionConfig(),
    'production': PrecisionConfig().get_optimized_for_web_service(),
    'high_performance': PrecisionConfig(
        database=DatabaseConfig(pool_size=20, cache_size=-128000),
        api=APIConfig(max_concurrent_requests=100),
        performance=PerformanceConfig(cache_size=5000),
        search=SearchConfig(max_items=1000)
    ),
    'minimal': PrecisionConfig(
        database=DatabaseConfig(pool_size=2),
        api=APIConfig(max_concurrent_requests=5),
        performance=PerformanceConfig(enable_caching=False),
        search=SearchConfig(max_items=50)
    )
}

def load_config(config_path: str = "config.json", preset: str = None) -> PrecisionConfig:
    """Load configuration with optional preset"""
    if preset and preset in PRESETS:
        config = PRESETS[preset]
        logger.info(f"Using configuration preset: {preset}")
    else:
        config = PrecisionConfig.from_file(config_path)
    
    # Validate configuration
    if not config.validate():
        logger.warning("Configuration validation failed, using defaults")
        config = PrecisionConfig()
    
    return config


