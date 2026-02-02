"""
AI Factory for creating analyzers from different providers.

Supports:
- Groq (cloud): Fast inference, requires API key
- Ollama (local): Private, no API key needed, runs on your machine

Usage:
    from scraper.ai_factory import create_analyzer, AIProvider

    # Auto-detect best available provider
    ai = create_analyzer()

    # Force specific provider
    ai = create_analyzer(provider=AIProvider.GROQ, model="smart")
    ai = create_analyzer(provider=AIProvider.OLLAMA, model="phi3")
"""

import os
from enum import Enum
from typing import Optional, Union
from dataclasses import dataclass

from .ai import AIAnalyzer, AIResponse
from .ai_local import OllamaAnalyzer, LocalAIResponse, is_ollama_available


class AIProvider(Enum):
    """Supported AI providers."""
    GROQ = "groq"       # Cloud-based, fast, requires API key
    OLLAMA = "ollama"   # Local, private, requires Ollama installed
    AUTO = "auto"       # Auto-detect best available


@dataclass
class ProviderInfo:
    """Information about an AI provider."""
    name: str
    available: bool
    reason: str = ""


def check_groq_available() -> ProviderInfo:
    """Check if Groq is available (API key set)."""
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        return ProviderInfo(name="Groq", available=True)
    return ProviderInfo(
        name="Groq",
        available=False,
        reason="GROQ_API_KEY not set in environment"
    )


def check_ollama_available() -> ProviderInfo:
    """Check if Ollama is available (installed and running)."""
    if is_ollama_available():
        return ProviderInfo(name="Ollama", available=True)
    return ProviderInfo(
        name="Ollama",
        available=False,
        reason="Ollama not installed or server not running"
    )


def get_available_providers() -> dict[str, ProviderInfo]:
    """Get availability status of all providers."""
    return {
        "groq": check_groq_available(),
        "ollama": check_ollama_available(),
    }


def create_analyzer(
    provider: AIProvider = AIProvider.AUTO,
    model: Optional[str] = None,
    verbose: bool = True
) -> Union[AIAnalyzer, OllamaAnalyzer]:
    """
    Create an AI analyzer from the specified provider.

    Args:
        provider: Which AI provider to use (GROQ, OLLAMA, or AUTO)
        model: Model name (provider-specific). If None, uses default.
        verbose: Print provider selection info

    Returns:
        AIAnalyzer (Groq) or OllamaAnalyzer (Ollama)

    Raises:
        RuntimeError: If no providers are available

    Examples:
        # Auto-select best available
        ai = create_analyzer()

        # Use Groq with specific model
        ai = create_analyzer(provider=AIProvider.GROQ, model="smart")

        # Use local Ollama
        ai = create_analyzer(provider=AIProvider.OLLAMA, model="phi3")
    """
    providers = get_available_providers()

    if provider == AIProvider.AUTO:
        # Prefer Groq (faster) if available, fall back to Ollama
        if providers["groq"].available:
            provider = AIProvider.GROQ
        elif providers["ollama"].available:
            provider = AIProvider.OLLAMA
        else:
            # List why each failed
            reasons = [f"  - {p.name}: {p.reason}" for p in providers.values()]
            raise RuntimeError(
                "No AI providers available:\n" + "\n".join(reasons) +
                "\n\nTo fix:\n"
                "  - For Groq: Set GROQ_API_KEY environment variable\n"
                "  - For Ollama: Install from https://ollama.ai and run 'ollama serve'"
            )

    # Create the selected provider
    if provider == AIProvider.GROQ:
        if not providers["groq"].available:
            raise RuntimeError(f"Groq not available: {providers['groq'].reason}")

        model = model or "smart"  # Default Groq model
        if verbose:
            print(f"🌐 Using Groq (cloud) with model: {model}")
        return AIAnalyzer(model=model)

    elif provider == AIProvider.OLLAMA:
        if not providers["ollama"].available:
            raise RuntimeError(f"Ollama not available: {providers['ollama'].reason}")

        model = model or "phi3"  # Default Ollama model
        if verbose:
            print(f"🏠 Using Ollama (local) with model: {model}")
        return OllamaAnalyzer(model=model)

    else:
        raise ValueError(f"Unknown provider: {provider}")


# Convenience functions
def create_groq_analyzer(model: str = "smart") -> AIAnalyzer:
    """Create a Groq cloud analyzer."""
    return create_analyzer(provider=AIProvider.GROQ, model=model, verbose=False)


def create_local_analyzer(model: str = "phi3") -> OllamaAnalyzer:
    """Create a local Ollama analyzer."""
    return create_analyzer(provider=AIProvider.OLLAMA, model=model, verbose=False)
