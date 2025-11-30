"""
API Configuration Management

This module provides a simple way to manage API keys and configuration
for external services like weather APIs, STAC APIs, etc.

Loads configuration from config.json file in the project root.

Usage:
    from config import get_api_key, get_api_url
    
    # Get API key
    weather_key = get_api_key('weather')
    
    # Get API URL
    stac_url = get_api_url('stac')
"""

import json
from typing import Optional, Dict, Any
from pathlib import Path


class APIConfig:
    """
    Simple API configuration manager.
    
    Loads configuration from config.json file in project root.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize API configuration.
        
        Args:
            config_file: Path to JSON config file (default: config.json in project root)
        """
        # Determine config file path
        if config_file is None:
            project_root = Path(__file__).parent.parent
            config_file = project_root / 'config.json'
        else:
            config_file = Path(config_file)
        
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        
        # Load from JSON file if it exists
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {config_file}: {e}")
                self._config = {}
    
    def get(self, service: str, key: str = 'api_key', default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value for a service.
        
        Args:
            service: Service name (e.g., 'weather', 'stac')
            key: Configuration key (default: 'api_key')
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        service_config = self._config.get(service, {})
        return service_config.get(key, default)


# Global configuration instance
_global_config: Optional[APIConfig] = None


def get_config() -> APIConfig:
    """Get the global API configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = APIConfig()
    return _global_config


def get_api_key(service: str, key: str = 'api_key') -> Optional[str]:
    """
    Get an API key for a service.
    
    Args:
        service: Service name (e.g., 'weather', 'stac')
        key: Configuration key (default: 'api_key')
    
    Returns:
        API key or None if not found
    """
    return get_config().get(service, key)


def get_api_url(service: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an API URL for a service.
    
    Args:
        service: Service name (e.g., 'stac')
        default: Default URL if not configured
    
    Returns:
        API URL or default
    """
    return get_config().get(service, 'api_url', default)

