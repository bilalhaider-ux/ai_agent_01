"""LLM provider factory used by the LangGraph nodes."""

from typing import Optional

from .config import AgentConfig, ProviderType


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
    if selected_provider == "openai":
        if not cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model or cfg.openai_model, api_key=cfg.openai_api_key, temperature=temperature)
    if selected_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model or cfg.ollama_model, base_url=cfg.ollama_base_url, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: '{selected_provider}'.")