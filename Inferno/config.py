"""
LLM Configuration Management for Inferno.

Loads LLM provider settings from environment variables and provides
configured provider instances.

Environment Variables:
    LLM_PROVIDER: Provider name (openai, anthropic, deepseek, ollama)
    LLM_MODEL: Model name (provider-specific)
    LLM_API_KEY: API key for the provider
    LLM_BASE_URL: Optional custom base URL
    LLM_REASONING_EFFORT: Reasoning effort level (low, medium, high)

Example:
    from config import LLMConfig
    
    config = LLMConfig()
    client = config.get_provider()
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

from llm_provider import LLMProvider, create_llm_provider

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LLMConfig:
    """
    LLM provider configuration from environment variables.
    
    Provides a centralized way to configure and instantiate LLM providers
    based on environment settings.
    """
    
    def __init__(self):
        """
        Load configuration from environment variables.
        
        Loads:
            - Provider selection (default: openai)
            - Model name (default: gpt-5)
            - API credentials
            - Optional base URL
            - Reasoning configuration
        """
        # Provider selection
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-5")
        
        # API credentials (with backward compatibility)
        self.api_key = self._get_api_key()
        self.base_url = os.getenv("LLM_BASE_URL")
        
        # Reasoning configuration
        self.reasoning_effort = os.getenv("LLM_REASONING_EFFORT", "high")
        
        # Validate configuration
        self._validate_config()
        
        logger.info(
            f"LLM Config loaded: provider={self.provider}, model={self.model}, "
            f"reasoning_effort={self.reasoning_effort}"
        )
    
    def _get_api_key(self) -> Optional[str]:
        """
        Get API key with backward compatibility.
        
        Tries LLM_API_KEY first, then falls back to provider-specific keys:
        - OPENAI_API_KEY for OpenAI
        - ANTHROPIC_API_KEY for Anthropic
        - DEEPSEEK_API_KEY for DeepSeek
        
        Returns:
            API key or None (for Ollama which doesn't need one)
        """
        # Try generic LLM_API_KEY first
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            return api_key
        
        # Fall back to provider-specific keys for backward compatibility
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == "deepseek":
            return os.getenv("DEEPSEEK_API_KEY")
        elif self.provider == "ollama":
            return None  # Ollama doesn't require API key
        
        return None
    
    def _validate_config(self):
        """
        Validate configuration and warn about potential issues.
        """
        # Check if API key is required but missing
        if self.provider in ["openai", "anthropic", "deepseek"] and not self.api_key:
            logger.warning(
                f"No API key found for provider '{self.provider}'. "
                f"Set LLM_API_KEY or {self.provider.upper()}_API_KEY environment variable."
            )
        
        # Validate reasoning effort
        valid_efforts = ["low", "medium", "high"]
        if self.reasoning_effort not in valid_efforts:
            logger.warning(
                f"Invalid reasoning effort: '{self.reasoning_effort}'. "
                f"Valid options: {valid_efforts}. Using 'high' as default."
            )
            self.reasoning_effort = "high"
    
    def get_provider(self) -> LLMProvider:
        """
        Get configured LLM provider instance.
        
        Returns:
            Configured LLMProvider instance ready to use
            
        Raises:
            ValueError: If configuration is invalid
            ImportError: If required provider package is not installed
        """
        return create_llm_provider(
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def get_config_summary(self) -> dict:
        """
        Get configuration summary for logging/debugging.
        
        Returns:
            Dictionary with configuration details (API key masked)
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "base_url": self.base_url or "(default)",
            "reasoning_effort": self.reasoning_effort
        }
