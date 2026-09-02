import json
import re
from abc import ABC, abstractmethod
from typing import TypeVar

from langchain_ollama import ChatOllama
from pydantic import BaseModel

from app.core.exceptions import DocumentParsingError

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)
MAX_DOCUMENT_CHARACTERS = 60_000


def _extract_json_block(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"(\{[\s\S]*\})", cleaned)
    if match:
        return match.group(1)
    return cleaned


class StructuredExtractionClient(ABC):
    """Contract for extracting a Pydantic model from unstructured text."""

    @abstractmethod
    async def extract(
        self,
        text: str,
        schema: type[StructuredModel],
        instructions: str,
    ) -> StructuredModel:
        """Extract and validate structured data."""


class OllamaStructuredExtractionClient(StructuredExtractionClient):
    """Use an Ollama chat model for schema-constrained extraction."""

    def __init__(self, *, model: str, base_url: str) -> None:
        self._model_name = model
        self._base_url = base_url
        self._json_model: ChatOllama | None = ChatOllama(
            model=model, base_url=base_url, temperature=0, format="json"
        )
        self._model: ChatOllama = ChatOllama(model=model, base_url=base_url, temperature=0)

    async def extract(
        self,
        text: str,
        schema: type[StructuredModel],
        instructions: str,
    ) -> StructuredModel:
        """Extract a validated model from document text using multiple fallback strategies."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        doc_slice = text[:MAX_DOCUMENT_CHARACTERS]
        prompt = (
            f"{instructions}\n\n"
            "Use only facts present in the document. Use empty strings or lists "
            "when a field is absent; never invent information.\n"
            "You MUST return ONLY a single valid JSON object strictly matching this schema (no preamble, no markdown wrap):\n"
            f"{schema_json}\n\n"
            f"DOCUMENT:\n{doc_slice}"
        )

        last_error: Exception | None = None

        # Strategy 1: Prompt with native format="json" sampler enforcement
        if self._json_model is not None and hasattr(self._json_model, "ainvoke"):
            try:
                resp = await self._json_model.ainvoke(prompt)
                raw_text = getattr(resp, "content", resp)
                clean_json = _extract_json_block(str(raw_text))
                return schema.model_validate_json(clean_json)
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        # Strategy 2: with_structured_output json_schema
        if hasattr(self._model, "with_structured_output"):
            try:
                structured_model = self._model.with_structured_output(
                    schema,
                    method="json_schema",
                )
                result = await structured_model.ainvoke(prompt)
                return result if isinstance(result, schema) else schema.model_validate(result)
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        # Strategy 3: Raw model invocation with regex JSON block extraction
        if hasattr(self._model, "ainvoke"):
            try:
                resp = await self._model.ainvoke(prompt)
                raw_text = getattr(resp, "content", resp)
                clean_json = _extract_json_block(str(raw_text))
                return schema.model_validate_json(clean_json)
            except Exception as exc:
                last_error = exc

        raise DocumentParsingError(self._error_message(last_error)) from last_error

    def _error_message(self, error: Exception | None) -> str:
        error_text = str(error).casefold() if error else ""
        if "model" in error_text and "not found" in error_text:
            return (
                f"Ollama model '{self._model_name}' is not installed. "
                f"Run: ollama pull {self._model_name}"
            )
        if "connection" in error_text or "connect" in error_text:
            return "Ollama is unavailable. Start Ollama and retry the request"
        return (
            f"Ollama model '{self._model_name}' could not produce the required "
            "structured document response"
        )
