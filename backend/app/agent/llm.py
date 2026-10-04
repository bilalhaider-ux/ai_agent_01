"""LLM provider factory used by the LangGraph nodes."""

from typing import Any, Optional, Sequence

from .config import AgentConfig, ProviderType


def _is_retryable_provider_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in ("429", "rate limit", "quota", "timeout", "temporarily", "503", "500"))


class FallbackChatModel:
    """Runnable facade that fails over between configured chat models."""

    def __init__(self, models: Sequence[Any]):
        self._models = list(models)

    def invoke(self, messages: Any) -> Any:
        last_error: Exception | None = None
        for model in self._models:
            try:
                return model.invoke(messages)
            except Exception as error:
                last_error = error
                if not _is_retryable_provider_error(error):
                    raise
        raise last_error or RuntimeError("No LLM model is configured.")

    def with_structured_output(self, schema: Any) -> "FallbackStructuredModel":
        return FallbackStructuredModel([model.with_structured_output(schema) for model in self._models])


class FallbackStructuredModel:
    def __init__(self, models: Sequence[Any]):
        self._models = list(models)

    def invoke(self, messages: Any) -> Any:
        last_error: Exception | None = None
        for model in self._models:
            try:
                return model.invoke(messages)
            except Exception as error:
                last_error = error
                if not _is_retryable_provider_error(error):
                    raise
        raise last_error or RuntimeError("No structured LLM model is configured.")


def get_llm(
    provider: Optional[ProviderType] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    config: Optional[AgentConfig] = None,
):
    """Create the configured LangChain chat model without exposing secrets."""
    cfg = config or AgentConfig()
    selected_provider = (provider or cfg.provider or "mistral").lower()

    if selected_provider == "mock":
        from .mock_llm import MockAnalyticsChatModel

        return MockAnalyticsChatModel()
    if selected_provider == "mistral":
        if not cfg.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required when LLM_PROVIDER=mistral.")
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model=model or cfg.mistral_model,
            api_key=cfg.mistral_api_key,
            temperature=temperature,
        )
    if selected_provider == "gemini":
        if not cfg.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini.")
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_names = [model or cfg.gemini_model, *(cfg.gemini_fallback_models or [])]
        unique_model_names = list(dict.fromkeys(name for name in model_names if name))
        return FallbackChatModel([
            ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=cfg.gemini_api_key,
                temperature=temperature,
            )
            for model_name in unique_model_names
        ])
    if selected_provider == "openai":
        if not cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model or cfg.openai_model, api_key=cfg.openai_api_key, temperature=temperature)
    if selected_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model or cfg.ollama_model, base_url=cfg.ollama_base_url, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: '{selected_provider}'.")