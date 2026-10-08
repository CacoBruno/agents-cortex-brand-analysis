from __future__ import annotations

from pathlib import Path

from cortex_brand_analysis.domain.audit import AuditRun


class JsonlAuditStore:
    def __init__(self, path: str | Path = ".data/audit/runs.jsonl") -> None:
        self.path = Path(path)

    def append(self, run: AuditRun) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(run.model_dump_json() + "\n")

    def list_runs(self, limit: int = 100) -> list[AuditRun]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        rows = [AuditRun.model_validate_json(line) for line in lines if line.strip()]
        return rows[-limit:][::-1]
