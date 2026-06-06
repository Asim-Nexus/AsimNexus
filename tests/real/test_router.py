#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade model router tests
ASIMNEXUS Model Router Tests
============================
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.router import RouterManager, setup_router_routes, RouteRequest, ChatRequest

class TestRouterManager:
    """Test suite for RouterManager class."""

    def test_privacy_classification(self):
        router = RouterManager()
        # Public
        assert router.classify_privacy("What is the capital of Nepal?") == "public"
        
        # Confidential
        assert router.classify_privacy("My bank balance is $500.") == "confidential"
        assert router.classify_privacy("Here is the contract draft for project.") == "confidential"

        # Highly Sensitive
        assert router.classify_privacy("My citizen ID is 12-345-6789.") == "highly_sensitive"
        assert router.classify_privacy("The root password is admin123!") == "highly_sensitive"

    def test_cloud_trust_tier_selection(self):
        router = RouterManager()
        # Public
        assert router.get_cloud_trust_tier("openai", "public") == "trusted_cloud"
        assert router.get_cloud_trust_tier("any_third_party", "public") == "trusted_cloud"

        # Confidential
        assert router.get_cloud_trust_tier("openai", "confidential") == "trusted_cloud"
        assert router.get_cloud_trust_tier("unknown_cloud", "confidential") == "forbidden_cloud"

        # Highly Sensitive
        assert router.get_cloud_trust_tier("openai", "highly_sensitive") == "forbidden_cloud"
        assert router.get_cloud_trust_tier("any", "highly_sensitive") == "forbidden_cloud"

    def test_determine_route_privacy_blocking(self):
        router = RouterManager()
        
        # Public
        res_pub = router.determine_route("Hello world", "public", "personal")
        assert res_pub["allowed_cloud"] is True
        assert res_pub["target_tier"] == "local_first"

        # Highly Sensitive
        res_sens = router.determine_route("Root credentials", "highly_sensitive", "personal")
        assert res_sens["allowed_cloud"] is False
        assert res_sens["target_tier"] == "local_only"
        assert "forbidden" in res_sens["reason"]

    @pytest.mark.asyncio
    async def test_execute_chat_no_cloud_block_for_highly_sensitive(self):
        # Local model offline, no cloud allowed
        local_checker = lambda: False
        async def mock_cloud_runner(prompt, user_id):
            return {"response": "Mock cloud output", "model": "openai"}
            
        router = RouterManager(local_checker, mock_cloud_runner)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await router.execute_chat("Secret passwords", "highly_sensitive", "personal")
        assert exc_info.value.status_code == 400
        assert "forbidden" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_execute_chat_cloud_fallback_for_public(self):
        # Local model offline, cloud allowed for public
        local_checker = lambda: False
        async def mock_cloud_runner(prompt, user_id):
            return {"response": "Mock cloud output", "model": "openai"}
            
        router = RouterManager(local_checker, mock_cloud_runner)
        
        res = await router.execute_chat("What is Python?", "public", "personal")
        assert res["success"] is True
        assert res["source"] == "cloud"
        assert res["response"] == "Mock cloud output"


class TestRouterRoutes:
    """Test suite for integrated API router routes."""

    @pytest.fixture
    def app(self):
        app = FastAPI()
        local_checker = lambda: False
        async def mock_cloud_runner(prompt, user_id):
            return {"response": "Mock cloud output", "model": "openai"}
        setup_router_routes(app, local_checker, mock_cloud_runner)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_route_endpoint(self, client):
        # Public route
        resp = client.post("/api/router/route", json={
            "message": "Hello how are you",
            "privacy_classification": "public",
            "mode": "personal"
        })
        assert resp.status_code == 200
        assert resp.json()["allowed_cloud"] is True
        assert resp.json()["privacy_classification"] == "public"

        # Highly Sensitive auto-detect
        resp_sens = client.post("/api/router/route", json={
            "message": "My password is admin!",
            "privacy_classification": "public",
            "mode": "personal"
        })
        assert resp_sens.status_code == 200
        assert resp_sens.json()["allowed_cloud"] is False
        assert resp_sens.json()["privacy_classification"] == "highly_sensitive"

    def test_chat_fallback_flow(self, client):
        # Public - allowed to fallback to cloud mock
        resp = client.post("/api/router/chat", json={
            "prompt": "Hello",
            "privacy_classification": "public"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["source"] == "cloud"

        # Highly sensitive - blocked from cloud fallback
        resp_sens = client.post("/api/router/chat", json={
            "prompt": "My secret password is 12345",
            "privacy_classification": "highly_sensitive"
        })
        assert resp_sens.status_code == 400
        assert "forbidden" in resp_sens.json()["detail"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
