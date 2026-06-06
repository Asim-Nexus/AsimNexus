#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade tool execution pipeline tests
ASIMNEXUS Tool Pipeline Tests
=============================
"""

import os
import gc
import time
import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.tools import ToolPipeline, setup_tools_routes, ToolExecutionRequest, ApproveToolRequest

class TestToolPipeline:
    """Test suite for ToolPipeline 6-stage execution."""

    @pytest.fixture
    def temp_db(self):
        from core.policy_gate import reset_policy_gate
        reset_policy_gate()
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        reset_policy_gate()
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def pipeline(self, temp_db):
        return ToolPipeline(temp_db)

    @pytest.fixture
    def clean_audit_log(self):
        audit_path = Path("data/cognitive_firewall.jsonl")
        audit_path.unlink(missing_ok=True)
        yield
        audit_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_successful_safe_tool_execution(self, pipeline, clean_audit_log):
        # Register a simple safe mock tool
        def mock_add(x: int, y: int):
            return {"sum": x + y}

        pipeline.register_tool("mock_add", mock_add)
        
        # Override policy rule for mock_add to auto-approve
        from core.policy_gate import PolicyRule, ActionCategory, ActionRisk
        pipeline.policy_gate.add_rule(PolicyRule(
            id="rule_mock_add",
            name="Mock Add",
            description="Adds numbers",
            category=ActionCategory.EXTERNAL_API,
            risk_level=ActionRisk.LOW,
            auto_approve=True,
            conditions={"action_type": "mock_add"}
        ))

        res = await pipeline.execute("mock_add", {"x": 5, "y": 10}, "external_api")
        assert res["status"] == "executed"
        assert res["result"]["sum"] == 15

        # Check audit trail
        audit_path = Path("data/cognitive_firewall.jsonl")
        assert audit_path.exists()
        lines = audit_path.read_text().splitlines()
        stages = [json.loads(line)["stage"] for line in lines]
        assert "1_DECISION" in stages
        assert "5_EXECUTION" in stages
        assert "6_AUDIT" in stages

    @pytest.mark.asyncio
    async def test_validation_boundary_failure(self, pipeline):
        # Validation error for writing files to system directories
        with pytest.raises(PermissionError, match="Security block"):
            await pipeline.execute("write_file", {"path": "C:/Windows/System32/config.txt", "content": "hack"}, "file_operation")

    @pytest.mark.asyncio
    async def test_approval_pending_and_human_resolution(self, pipeline, clean_audit_log):
        # Tool that requires approval
        def dangerous_action():
            return {"deleted": True}

        pipeline.register_tool("dangerous_action", dangerous_action)

        from core.policy_gate import PolicyRule, ActionCategory, ActionRisk
        pipeline.policy_gate.add_rule(PolicyRule(
            id="rule_dangerous_action",
            name="Dangerous Action",
            description="Deletes stuff",
            category=ActionCategory.SYSTEM_COMMAND,
            risk_level=ActionRisk.HIGH,
            auto_approve=False,
            conditions={"action_type": "dangerous_action"}
        ))

        # 1. Execute should return pending approval
        res = await pipeline.execute("dangerous_action", {}, "system_command")
        assert res["status"] == "pending_approval"
        req_id = res["request_id"]
        assert req_id in pipeline.pending_tools

        # 2. Resuming execution with Human approval
        exec_res = pipeline.approve_pending(req_id, "human_founder")
        assert exec_res["status"] == "executed"
        assert exec_res["result"]["deleted"] is True
        assert req_id not in pipeline.pending_tools


class TestToolsRoutes:
    """Test suite for integrated tools API endpoints."""

    @pytest.fixture
    def temp_db(self):
        from core.policy_gate import reset_policy_gate
        reset_policy_gate()
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        yield path
        reset_policy_gate()
        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def app(self, temp_db):
        app = FastAPI()
        setup_tools_routes(app, temp_db)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.fixture
    def clean_audit_log(self):
        audit_path = Path("data/cognitive_firewall.jsonl")
        audit_path.unlink(missing_ok=True)
        yield
        audit_path.unlink(missing_ok=True)

    def test_routes_integration_flow(self, client, clean_audit_log):
        # 1. Execute tool that requires approval by default (file write rule is auto_approve = False)
        resp = client.post("/api/tools/execute", json={
            "tool_name": "write_file",
            "parameters": {"path": "test_doc.txt", "content": "Hello Trust Path"},
            "category": "file_operation"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending_approval"
        req_id = data["request_id"]

        # 2. Get pending approvals
        p_resp = client.get("/api/tools/pending")
        assert p_resp.status_code == 200
        assert len(p_resp.json()) == 1
        assert p_resp.json()[0]["id"] == req_id

        # 3. Approve via API
        a_resp = client.post("/api/tools/approve", json={
            "request_id": req_id,
            "decision": True,
            "approver": "test_operator"
        })
        assert a_resp.status_code == 200
        assert a_resp.json()["status"] == "executed"
        assert a_resp.json()["result"]["success"] is True

        # Check file was written
        p = Path("test_doc.txt")
        assert p.exists()
        assert p.read_text() == "Hello Trust Path"
        p.unlink()

        # 4. Read audit logs via API
        aud_resp = client.get("/api/tools/audit")
        assert aud_resp.status_code == 200
        assert len(aud_resp.json()) > 0
        stages = [entry["stage"] for entry in aud_resp.json()]
        assert "1_DECISION" in stages
        assert "6_AUDIT" in stages


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
