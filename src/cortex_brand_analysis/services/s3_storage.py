from __future__ import annotations

import json

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.news_ingestion import EnrichedNews


class S3NewsStorage:
    """Idempotent S3 writer: the object key is derived from the deterministic news ID."""

    def __init__(
        self,
        settings: Settings,
        bucket: str = "cortex-data-lake-landing-area",
        prefix: str = "pr/cortex-staging/oraculo/",
    ) -> None:
        self.settings = settings
        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/"

    def store(self, items: list[EnrichedNews], platform_url: str) -> list[str]:
        if not items:
            return []

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 ingestion") from exc

        client = boto3.client("s3", region_name=self.settings.aws_region)
        keys: list[str] = []
        for item in items:
            key = f"{self.prefix}{item.idempotency_key}.json"
            payload = item.model_dump(mode="json")
            payload["plataforma_url"] = platform_url
            client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json; charset=utf-8",
                Metadata={"idempotency-key": item.idempotency_key},
            )
            keys.append(key)
        return keys
