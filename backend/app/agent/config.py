"""Runtime configuration for the analytics agent."""

import os
from typing import Literal, Optional
from dataclasses import dataclass
try:
    from dotenv import load_dotenv

    # Load .env file if available
    load_dotenv()
except ImportError:
    pass

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
            self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()  # type: ignore
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
            self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
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
