"""
VOLT AI Manager - Multi-Provider LLM Integration
Uses Mozilla.ai any-llm-sdk for unified LLM access
Supports: Ollama, OpenAI, Anthropic, Mistral, and more
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.utils.logger import get_logger


@dataclass
class LLMProvider:
    """Configuration for an LLM provider"""

    id: str
    name: str
    api_key_env: str
    default_model: str
    models: List[str]


class VOLTAIManager:
    """
    Unified LLM manager for VOLT trading system
    Uses Mozilla.ai any-llm-sdk for multi-provider support
    """

    # Supported providers
    PROVIDERS = {
        "ollama": LLMProvider(
            id="ollama",
            name="Ollama (Local)",
            api_key_env="",
            default_model="dolphin-llama3:latest",
            models=[
                "dolphin-llama3:latest",
                "gemma3:latest",
                "qwen2.5-coder:7b",
                "llama3.2:3b",
                "mistral:latest",
                "phi4:latest",
            ],
        ),
        "openai": LLMProvider(
            id="openai",
            name="OpenAI",
            api_key_env="OPENAI_API_KEY",
            default_model="gpt-4o-mini",
            models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        ),
        "anthropic": LLMProvider(
            id="anthropic",
            name="Anthropic Claude",
            api_key_env="ANTHROPIC_API_KEY",
            default_model="claude-3-5-sonnet-20241022",
            models=[
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307",
            ],
        ),
        "mistral": LLMProvider(
            id="mistral",
            name="Mistral AI",
            api_key_env="MISTRAL_API_KEY",
            default_model="mistral-small-latest",
            models=[
                "mistral-small-latest",
                "mistral-medium-latest",
                "mistral-large-latest",
            ],
        ),
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(__name__)
        self.config = config or {}

        # Default provider
        self.current_provider = self.config.get("default_provider", "ollama")
        self.current_model = self.config.get("default_model", "dolphin-llama3:latest")

        # any-llm client
        self._client = None
        self._initialize_client()

        self.logger.info(
            f"🤖 VOLT AI Manager initialized with provider: {self.current_provider}"
        )

    def _initialize_client(self):
        """Initialize the any-llm client"""
        try:
            from any_llm import AnyLLM, completion, acompletion

            # Get provider config
            provider = self.PROVIDERS.get(self.current_provider)
            if not provider:
                self.logger.warning(
                    f"Unknown provider {self.current_provider}, falling back to ollama"
                )
                self.current_provider = "ollama"
                provider = self.PROVIDERS["ollama"]

            # Get API key if needed
            api_key = None
            if provider.api_key_env:
                api_key = os.environ.get(provider.api_key_env)
                if not api_key:
                    self.logger.warning(
                        f"No API key found for {provider.name} ({provider.api_key_env})"
                    )

            # Create client based on provider
            if self.current_provider == "ollama":
                # Ollama - local, no API key needed
                self._client = AnyLLM.create(provider="ollama")
            elif api_key:
                self._client = AnyLLM.create(
                    provider=self.current_provider, api_key=api_key
                )
            else:
                self.logger.warning(
                    f"No API key available for {provider.name}, using Ollama fallback"
                )
                self._client = AnyLLM.create(provider="ollama")
                self.current_provider = "ollama"

            self.logger.info(f"✅ Connected to {provider.name}")
            self._completion = completion

        except Exception as e:
            self.logger.error(f"Failed to initialize any-llm client: {e}")
            self._client = None
            self._completion = None

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.6,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Generate a completion using the current provider

        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Override model (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            {"content": str, "model": str, "provider": str}
        """
        try:
            from any_llm import acompletion

            effective_model = model or self.current_model

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await acompletion(
                model=effective_model,
                provider=self.current_provider,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = (
                response.choices[0].message.content
                if hasattr(response, "choices")
                else str(response)
            )

            return {
                "content": content,
                "model": effective_model,
                "provider": self.current_provider,
                "success": True,
            }

        except Exception as e:
            self.logger.error(f"LLM completion error: {e}")
            return {
                "error": str(e),
                "content": "",
                "model": self.current_model,
                "provider": self.current_provider,
                "success": False,
            }

    def switch_provider(self, provider_id: str, model: Optional[str] = None) -> bool:
        """
        Switch to a different LLM provider

        Args:
            provider_id: Provider ID (ollama, openai, anthropic, mistral)
            model: Optional specific model

        Returns:
            True if successful
        """
        if provider_id not in self.PROVIDERS:
            self.logger.error(f"Unknown provider: {provider_id}")
            return False

        self.current_provider = provider_id
        if model:
            self.current_model = model
        else:
            self.current_model = self.PROVIDERS[provider_id].default_model

        self._initialize_client()
        return True

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers and their status"""
        available = []

        for provider_id, provider in self.PROVIDERS.items():
            # Check if API key is available (except Ollama)
            has_key = True
            if provider.api_key_env:
                has_key = bool(os.environ.get(provider.api_key_env))

            # For Ollama, check if server is running
            ollama_ok = True
            if provider_id == "ollama":
                try:
                    import requests

                    r = requests.get("http://localhost:11434/api/tags", timeout=2)
                    ollama_ok = r.status_code == 200
                except:
                    ollama_ok = False

            status = "available" if (has_key or ollama_ok) else "no_api_key"

            available.append(
                {
                    "id": provider_id,
                    "name": provider.name,
                    "status": status,
                    "default_model": provider.default_model,
                    "models": provider.models,
                    "current_model": self.current_model
                    if self.current_provider == provider_id
                    else None,
                }
            )

        return available

    def get_status(self) -> Dict[str, Any]:
        """Get current AI manager status"""
        return {
            "current_provider": self.current_provider,
            "current_model": self.current_model,
            "providers": self.get_available_providers(),
        }


# Factory function for easy instantiation
def create_ai_manager(config: Optional[Dict[str, Any]] = None) -> VOLTAIManager:
    """Create a VOLT AI Manager instance"""
    return VOLTAIManager(config)
