"""Integration and Unit Tests for Phase 8 FastAPI Endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.job_runner import job_runner
from tests.conftest import run_coro

client = TestClient(app)


class TestAPIPhase8:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_upload_invalid_file_extension_rejected(self):
        resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"some plain text", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Only PDF documents are supported" in resp.json()["detail"]

    def test_upload_corrupt_pdf_magic_bytes_rejected(self):
        resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("corrupt.pdf", b"NOT_A_PDF_BYTES", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Invalid or corrupted PDF" in resp.json()["detail"]

    def test_upload_and_pipeline_execution_flow(self):
        # Use synthetic test PDF
        pdf_path = Path("eval/data/docs/REV_001_HI.pdf")
        assert pdf_path.exists()
        pdf_bytes = pdf_path.read_bytes()

        # 1. Upload
        upload_resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("REV_001_HI.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload_resp.status_code == 202
        data = upload_resp.json()
        assert "doc_id" in data
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "AI-assisted summary. Verify against the source document." in data["disclaimer"]

        job_id = data["job_id"]
        doc_id = data["doc_id"]

        # 2. Run Job to completion synchronously using run_coro
        run_coro(job_runner.execute_job(job_id))

        # 3. Check Job Status
        job_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert job_resp.status_code == 200
        job_data = job_resp.json()
        assert job_data["status"] == "completed"
        assert job_data["progress"] == 100

        # 4. Check Document Metadata
        doc_resp = client.get(f"/api/v1/documents/{doc_id}")
        assert doc_resp.status_code == 200
        assert doc_resp.json()["status"] == "completed"

        # 5. Check Brief Retrieval
        brief_resp = client.get(f"/api/v1/documents/{doc_id}/brief")
        assert brief_resp.status_code == 200
        brief_data = brief_resp.json()
        assert brief_data["doc_id"] == doc_id
        assert "AI-assisted summary. Verify against the source document." in brief_data["disclaimer"]
        assert brief_data["case_number"]["found"] is True

        # 6. Check Rules Compliance Report
        rules_resp = client.get(f"/api/v1/documents/{doc_id}/rules")
        assert rules_resp.status_code == 200
        rules_data = rules_resp.json()
        assert "rules_results" in rules_data
        assert rules_data["total_rules"] >= 1

        # 7. Check Conflicts Report
        conf_resp = client.get(f"/api/v1/documents/{doc_id}/conflicts")
        assert conf_resp.status_code == 200
        conf_data = conf_resp.json()
        assert "conflicts" in conf_data

        # 8. Check Follow-up Q&A
        qa_resp = client.post(
            "/api/v1/qa/ask",
            json={"doc_id": doc_id, "question": "इस वाद की स्थिति क्या है?"},
        )
        assert qa_resp.status_code == 200
        qa_data = qa_resp.json()
        assert "answer" in qa_data
        assert len(qa_data["citations"]) >= 1

    def test_admin_list_rules_and_audit_logs(self):
        # Test List Rules
        rules_resp = client.get("/api/v1/admin/rules")
        assert rules_resp.status_code == 200
        assert rules_resp.json()["total"] >= 1

        # Test Audit Logs
        audit_resp = client.get("/api/v1/admin/audit-logs")
        assert audit_resp.status_code == 200
        assert audit_resp.json()["total"] >= 1
