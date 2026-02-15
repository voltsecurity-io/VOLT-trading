"""
VOLT AnyLLM Adapter
Unified interface for multiple LLM providers using Mozilla's any-llm

This adapter allows VOLT to switch between providers (Ollama, OpenAI, Anthropic, Mistral, etc.)
without changing the code, and provides automatic fallback when providers fail.
"""

import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Provider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""

    provider: str
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.6
    max_tokens: int = 2048
    timeout: int = 60


class AnyLLMAdapter:
    """
    Adapter that provides a unified interface to multiple LLM providers
    using Mozilla's any-llm library.

    Features:
    - Single interface for all providers
    - Automatic fallback on failure
    - Provider switching without code changes
    - Cost and performance tracking
    """

    # Default models for each provider
    DEFAULT_MODELS = {
        Provider.OLLAMA: "qwen2.5-coder:7b",
        Provider.OPENAI: "gpt-4o-mini",
        Provider.ANTHROPIC: "claude-3-haiku-20240307",
        Provider.MISTRAL: "mistral-small-latest",
        Provider.GOOGLE: "gemini-2.0-flash",
    }

    # Fallback chain - when one fails, try the next
    FALLBACK_CHAIN = [
        Provider.OLLAMA,  # Local first (cheapest)
        Provider.OPENAI,  # Then OpenAI (fast)
        Provider.MISTRAL,  # Then Mistral (balanced)
        Provider.ANTHROPIC,  # Then Anthropic (quality)
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.current_provider = None
        self.current_model = None
        self.client = None
        self._init_providers()

    def _init_providers(self):
        """Initialize available providers based on API keys"""
        self.available_providers = []

        # Check which providers have API keys
        if os.environ.get("OLLAMA_HOST") or True:  # Ollama is local
            self.available_providers.append(Provider.OLLAMA)

        if os.environ.get("OPENAI_API_KEY"):
            self.available_providers.append(Provider.OPENAI)

        if os.environ.get("ANTHROPIC_API_KEY"):
            self.available_providers.append(Provider.ANTHROPIC)

        if os.environ.get("MISTRAL_API_KEY"):
            self.available_providers.append(Provider.MISTRAL)

        if os.environ.get("GOOGLE_API_KEY"):
            self.available_providers.append(Provider.GOOGLE)

        self.logger.info(
            f"Available providers: {[p.value for p in self.available_providers]}"
        )

    def _get_provider_config(self, provider: Provider) -> Dict[str, Any]:
        """Get configuration for a specific provider"""

        config = self.config.get(provider.value, {})

        base_config = {
            "model": config.get("model", self.DEFAULT_MODELS.get(provider, "default")),
            "temperature": config.get("temperature", 0.6),
            "max_tokens": config.get("max_tokens", 2048),
            "timeout": config.get("timeout", 60),
        }

        # Add provider-specific settings
        if provider == Provider.OLLAMA:
            base_config["provider"] = "ollama"
            base_config["api_base"] = os.environ.get(
                "OLLAMA_HOST", "http://localhost:11434"
            )

        elif provider == Provider.OPENAI:
            base_config["provider"] = "openai"
            base_config["api_key"] = os.environ.get("OPENAI_API_KEY")
            base_config["api_base"] = config.get(
                "api_base", "https://api.openai.com/v1"
            )

        elif provider == Provider.ANTHROPIC:
            base_config["provider"] = "anthropic"
            base_config["api_key"] = os.environ.get("ANTHROPIC_API_KEY")

        elif provider == Provider.MISTRAL:
            base_config["provider"] = "mistral"
            base_config["api_key"] = os.environ.get("MISTRAL_API_KEY")

        elif provider == Provider.GOOGLE:
            base_config["provider"] = "google"
            base_config["api_key"] = os.environ.get("GOOGLE_API_KEY")

        return base_config

    async def complete(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[Provider] = None,
        model: Optional[str] = None,
        fallback: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate completion using any-llm

        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            provider: Specific provider to use (optional)
            model: Specific model to use (optional)
            fallback: Whether to try fallback providers on failure
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            {"content": "...", "provider": "...", "model": "..."}
        """
        from any_llm import completion, acompletion

        # Determine which providers to try
        if provider:
            providers_to_try = [provider]
        elif fallback:
            providers_to_try = self.available_providers.copy()
        else:
            providers_to_try = (
                [self.available_providers[0]] if self.available_providers else []
            )

        last_error = None

        for p in providers_to_try:
            try:
                p_config = self._get_provider_config(p)

                # Override model if specified
                if model:
                    p_config["model"] = model

                # Merge additional kwargs
                p_config.update(kwargs)

                # Make the request
                self.logger.info(
                    f"Calling {p.value} with model {p_config.get('model')}"
                )

                response = await acompletion(
                    model=p_config.get("model"),
                    provider=p_config.get("provider"),
                    messages=messages,
                )

                # Extract content
                content = (
                    response.choices[0].message.content if response.choices else ""
                )

                self.current_provider = p
                self.current_model = p_config.get("model")

                self.logger.info(f"✅ {p.value} call successful")

                return {
                    "content": content,
                    "provider": p.value,
                    "model": self.current_model,
                    "raw_response": response,
                }

            except Exception as e:
                self.logger.warning(f"⚠️ {p.value} failed: {str(e)[:100]}")
                last_error = e
                continue

        # All providers failed
        error_msg = f"All providers failed. Last error: {last_error}"
        self.logger.error(f"❌ {error_msg}")

        return {
            "content": f"ERROR: {error_msg}",
            "provider": "none",
            "model": "none",
            "error": str(last_error),
        }

    async def complete_with_fallback(
        self,
        messages: List[Dict[str, str]],
        preferred_provider: Optional[Provider] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Complete with automatic fallback chain
        Tries preferred provider first, then falls back to others
        """

        if preferred_provider and preferred_provider in self.available_providers:
            # Put preferred first, then others
            providers = [preferred_provider] + [
                p for p in self.available_providers if p != preferred_provider
            ]
        else:
            providers = self.available_providers

        last_error = None

        for provider in providers:
            try:
                result = await self.complete(
                    messages=messages, provider=provider, fallback=False, **kwargs
                )

                if "error" not in result.get("content", "").lower():
                    return result

            except Exception as e:
                self.logger.warning(f"⚠️ {provider.value} failed, trying next...")
                last_error = e
                continue

        return {
            "content": f"ERROR: All providers exhausted. Last error: {last_error}",
            "provider": "none",
            "model": "none",
            "error": str(last_error),
        }

    def get_available_models(self, provider: Provider) -> List[str]:
        """Get available models for a provider"""
        try:
            from any_llm import AnyLLM

            client = AnyLLM.create(provider.value)
            models = client.list_models()
            return [m.id for m in models]
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []

    def estimate_cost(self, provider: Provider, model: str, tokens: int) -> float:
        """Estimate cost for a request (in USD)"""

        # Approximate pricing (per 1M tokens)
        pricing = {
            Provider.OPENAI: {
                "gpt-4o": 2.50,
                "gpt-4o-mini": 0.15,
                "gpt-4": 30.00,
                "gpt-3.5-turbo": 0.50,
            },
            Provider.ANTHROPIC: {
                "claude-3-opus": 15.00,
                "claude-3-sonnet": 3.00,
                "claude-3-haiku": 0.25,
            },
            Provider.MISTRAL: {
                "mistral-large": 2.00,
                "mistral-small": 0.20,
            },
            Provider.OLLAMA: 0.0,  # Local, free
            Provider.GOOGLE: {
                "gemini-2.0-flash": 0.0,  # Free tier
            },
        }

        provider_pricing = pricing.get(provider, {})
        rate = provider_pricing.get(model, 1.0)  # Default to $1/M if unknown

        return (tokens / 1_000_000) * rate


class MultiProviderAgent:
    """
    Agent wrapper that uses AnyLLMAdapter for LLM calls
    with automatic provider switching and fallback
    """

    def __init__(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None,
        preferred_provider: Provider = Provider.OLLAMA,
    ):
        self.agent_id = agent_id
        self.config = config or {}
        self.preferred_provider = preferred_provider
        self.llm_adapter = AnyLLMAdapter(config)
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    async def think(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate thought using the best available provider"""

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        result = await self.llm_adapter.complete_with_fallback(
            messages=messages, preferred_provider=self.preferred_provider
        )

        content = result.get("content", "")

        if "ERROR" in content:
            self.logger.error(f"Agent thinking failed: {content}")
            return "ERROR: Unable to generate response"

        return content

    async def think_with_context(
        self, prompt: str, context: Dict[str, Any], system_prompt: Optional[str] = None
    ) -> str:
        """Generate thought with additional context"""

        # Build context string
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])

        full_prompt = f"""Context:
{context_str}

Question: {prompt}"""

        return await self.think(full_prompt, system_prompt)


# Convenience function for VOLT
def create_agent(
    agent_id: str, provider: str = "ollama", model: Optional[str] = None
) -> MultiProviderAgent:
    """Factory function to create a multi-provider agent"""

    provider_enum = Provider(provider.lower()) if provider else Provider.OLLAMA

    return MultiProviderAgent(agent_id=agent_id, preferred_provider=provider_enum)
