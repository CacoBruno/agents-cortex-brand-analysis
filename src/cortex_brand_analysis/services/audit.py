from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar
from zoneinfo import ZoneInfo

from cortex_brand_analysis.domain.audit import AuditRun
from cortex_brand_analysis.services.audit_store import JsonlAuditStore

T = TypeVar("T")


class AuditService:
    def __init__(self, store: JsonlAuditStore) -> None:
        self.store = store

    def run(
        self,
        operation: str,
        func: Callable[[], T],
        *,
        input_summary: dict[str, object] | None = None,
        writes_external_state: bool = False,
        summarize_result: Callable[[T], dict[str, object]] | None = None,
    ) -> tuple[str, T]:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
        started_perf = time.perf_counter()

        try:
            result = func()
        except Exception as exc:
            finished_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
            self.store.append(
                AuditRun(
                    run_id=run_id,
                    operation=operation,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=int((time.perf_counter() - started_perf) * 1000),
                    status="error",
                    writes_external_state=writes_external_state,
                    input_summary=input_summary or {},
                    error_type=type(exc).__name__,
                    error_message=str(exc)[:1000],
                )
            )
            raise

        finished_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
        self.store.append(
            AuditRun(
                run_id=run_id,
                operation=operation,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=int((time.perf_counter() - started_perf) * 1000),
                status="success",
                writes_external_state=writes_external_state,
                input_summary=input_summary or {},
                result_summary=summarize_result(result) if summarize_result else {},
            )
        )
        return run_id, result
