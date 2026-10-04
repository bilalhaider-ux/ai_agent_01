"""Runtime configuration for the analytics agent.

Supports:
Mistral is the production provider. Mock remains available for tests; legacy
providers are retained for compatibility with existing CLI usage.
"""

import os
from typing import Literal, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

ProviderType = Literal["mistral", "gemini", "ollama", "openai", "mock"]


@dataclass
class AgentConfig:
    provider: Optional[ProviderType] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    mistral_api_key: Optional[str] = None
    mistral_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    gemini_fallback_models: Optional[list[str]] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    max_retries: Optional[int] = None
    execution_timeout_seconds: Optional[int] = None

    def __post_init__(self):
        if not self.provider:
            self.provider = os.getenv("LLM_PROVIDER", "mistral").lower()  # type: ignore
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_model:
            self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if self.mistral_api_key is None:
            self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not self.mistral_model:
            self.mistral_model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        if self.gemini_api_key is None:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.gemini_model:
            self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        if self.gemini_fallback_models is None:
            self.gemini_fallback_models = [
                item.strip()
                for item in os.getenv("GEMINI_FALLBACK_MODELS", "").split(",")
                if item.strip()
            ]
        if not self.ollama_base_url:
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if not self.ollama_model:
            self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        if self.max_retries is None:
            self.max_retries = int(os.getenv("MAX_RETRY_COUNT", "3"))
        if self.execution_timeout_seconds is None:
            self.execution_timeout_seconds = int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "45"))


def get_llm(
    provider: Optional[ProviderType] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    config: Optional[AgentConfig] = None
):
    """Factory creating the configured BaseChatModel instance.
    
    Args:
    provider: 'mistral', 'ollama', 'openai', or 'mock'. Defaults to config.provider.
        model: Model identifier (e.g. 'llama3.2' or 'gpt-4o-mini').
        temperature: Sampling temperature (default 0.0 for deterministic code/plans).
        config: Optional pre-loaded AgentConfig instance.
        
    Returns:
        Configured BaseChatModel instance.
    """
    cfg = config or AgentConfig()
    selected_provider = (provider or os.getenv("LLM_PROVIDER") or cfg.provider).lower()
    
    if selected_provider == "mock":
        from .mock_llm import MockAnalyticsChatModel
        return MockAnalyticsChatModel()

    elif selected_provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        if not cfg.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required when LLM_PROVIDER=mistral.")
        return ChatMistralAI(
            model=model or cfg.mistral_model,
            api_key=cfg.mistral_api_key,
            temperature=temperature,
        )
        
    elif selected_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not cfg.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        return ChatGoogleGenerativeAI(
            model=model or cfg.gemini_model,
            google_api_key=cfg.gemini_api_key,
            temperature=temperature,
        )

    elif selected_provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = cfg.openai_api_key
        if not api_key:
            raise ValueError(
                "OpenAI API key is missing! Please set OPENAI_API_KEY in your .env file "
                "or pass it via the environment."
            )
        selected_model = model or cfg.openai_model
        return ChatOpenAI(
            model=selected_model,
            api_key=api_key,
            temperature=temperature
        )
        
    elif selected_provider == "ollama":
        from langchain_ollama import ChatOllama
        selected_model = model or cfg.ollama_model
        return ChatOllama(
            model=selected_model,
            base_url=cfg.ollama_base_url,
            temperature=temperature
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{selected_provider}'. "
            "Supported options are 'mistral', 'ollama', 'openai', or 'mock'."
        )
