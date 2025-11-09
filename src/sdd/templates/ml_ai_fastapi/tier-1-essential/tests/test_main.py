"""
Tests for main FastAPI application
"""

import pytest
from httpx import AsyncClient  # type: ignore[import-not-found]


@pytest.mark.unit
class TestMainApp:
    """Test cases for main application endpoints."""

    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test root endpoint returns correct information."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    async def test_liveness_check(self, client: AsyncClient) -> None:
        """Test liveness check endpoint."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    async def test_readiness_check(self, client: AsyncClient) -> None:
        """Test readiness check endpoint."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
