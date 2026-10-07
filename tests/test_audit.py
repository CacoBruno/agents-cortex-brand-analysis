from pathlib import Path

from cortex_brand_analysis.services.audit import AuditService
from cortex_brand_analysis.services.audit_store import JsonlAuditStore


def test_audit_records_success(tmp_path: Path):
    store = JsonlAuditStore(tmp_path / "runs.jsonl")
    service = AuditService(store)

    run_id, result = service.run(
        "test.operation",
        lambda: {"rows": 3},
        input_summary={"x": 1},
        summarize_result=lambda value: {"rows": value["rows"]},
    )

    assert result["rows"] == 3
    runs = store.list_runs()
    assert runs[0].run_id == run_id
    assert runs[0].status == "success"
    assert runs[0].result_summary["rows"] == 3


def test_audit_records_errors(tmp_path: Path):
    store = JsonlAuditStore(tmp_path / "runs.jsonl")
    service = AuditService(store)

    try:
        service.run(
            "test.failure",
            lambda: (_ for _ in ()).throw(ValueError("boom")),
            writes_external_state=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    run = store.list_runs()[0]
    assert run.status == "error"
    assert run.writes_external_state is True
    assert run.error_type == "ValueError"
