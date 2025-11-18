"""
Unit tests for main application
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
class TestMainApp:
    """Test cases for main application."""

    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test root endpoint returns API information."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    async def test_docs_endpoint(self, client: AsyncClient) -> None:
        """Test API documentation endpoint."""
        response = await client.get("/docs")
        assert response.status_code == 200

    async def test_openapi_schema(self, client: AsyncClient) -> None:
        """Test OpenAPI schema endpoint."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    async def test_app_lifespan(self) -> None:
        """Test application lifespan startup and shutdown."""
        from unittest.mock import AsyncMock, patch

        from src.main import app as test_app
        from src.main import lifespan

        # Mock create_db_and_tables
        with patch("src.main.create_db_and_tables", new_callable=AsyncMock) as mock_create_db:
            with patch("src.main.logger") as mock_logger:
                # Run the lifespan context manager
                async with lifespan(test_app):
                    # Verify startup was called
                    assert mock_create_db.called
                    assert mock_logger.info.called

                # After exiting, shutdown logging should have been called
                shutdown_calls = [
                    call for call in mock_logger.info.call_args_list if "Shutting down" in str(call)
                ]
                assert len(shutdown_calls) > 0
