from __future__ import annotations

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.errors import ConfigurationError, UpstreamError
from cortex_brand_analysis.domain.rag import RagAnswer, RetrievedChunk


class OpenAIRagService:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for RAG")
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI, OpenAIError

        client = OpenAI(api_key=self.settings.openai_api_key)
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
        except OpenAIError as exc:
            raise UpstreamError("OpenAI embeddings request failed") from exc
        return [item.embedding for item in response.data]

    def answer(self, question: str, sources: list[RetrievedChunk]) -> RagAnswer:
        from openai import OpenAI, OpenAIError

        client = OpenAI(api_key=self.settings.openai_api_key)
        context = "\n\n".join(f"[{item.document_id}] {item.text}" for item in sources)
        try:
            response = client.responses.create(
                model="gpt-6-luna",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Você responde dúvidas sobre o produto Cortex PR. "
                            "Use somente o contexto fornecido. Se o contexto não for suficiente, "
                            "diga explicitamente que não há evidência suficiente. "
                            "Seja didático e não invente informações."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Contexto:\n{context}\n\nPergunta: {question}",
                    },
                ],
            )
        except OpenAIError as exc:
            raise UpstreamError("OpenAI answer request failed") from exc
        return RagAnswer(answer=response.output_text, sources=sources)
