"""Ollama-backed embedding service."""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_ollama import OllamaEmbeddings

from app.rag.config import RAGConfig
from app.rag.exceptions import VectorStoreConnectionError


class EmbeddingService(ABC):
    """Embedding provider contract."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""


class OllamaEmbeddingService(EmbeddingService):
    """Embed text through the configured Ollama model."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        config = config or RAGConfig()
        self._config = config
        self._model = OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.ollama_base_url,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""
        if not texts:
            return []
        try:
            return self._model.embed_documents(texts)
        except Exception as error:
            raise VectorStoreConnectionError(
                f"Failed to connect to Ollama embedding service at {self._config.ollama_base_url} "
                f"for model '{self._config.embedding_model}'. Ensure Ollama is running ('ollama serve') "
                f"and model is pulled ('ollama pull {self._config.embedding_model}')."
            ) from error

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query."""
        try:
            return self._model.embed_query(text)
        except Exception as error:
            raise VectorStoreConnectionError(
                f"Failed to connect to Ollama embedding service at {self._config.ollama_base_url} "
                f"for model '{self._config.embedding_model}'. Ensure Ollama is running ('ollama serve') "
                f"and model is pulled ('ollama pull {self._config.embedding_model}')."
            ) from error
