from __future__ import annotations

import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def get_default_llm(
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> Any:
    """
    Retorna o LLM padrão do projeto.
    """
    model_name = model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
    )


def get_default_embeddings(
    model: Optional[str] = None,
) -> Any:
    """
    Retorna o backend de embeddings padrão do projeto.
    """
    model_name = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    return OpenAIEmbeddings(
        model=model_name,
    )