"""
Integration tests for API endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestItemAPIIntegration:
    """Integration tests for Item API endpoints."""

    async def test_create_and_retrieve_item(self, integration_client: AsyncClient):
        """Test full cycle: create item and retrieve it."""
        # Create an item
        create_response = await integration_client.post(
            "/api/v1/items",
            json={
                "name": "Integration Test Item",
                "description": "Full stack test",
                "price": 29.99,
            },
        )
        assert create_response.status_code == 201
        created_item = create_response.json()
        assert created_item["name"] == "Integration Test Item"
        item_id = created_item["id"]

        # Retrieve the item
        get_response = await integration_client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        assert retrieved_item["id"] == item_id
        assert retrieved_item["name"] == "Integration Test Item"

    async def test_create_update_delete_workflow(self, integration_client: AsyncClient):
        """Test complete CRUD workflow."""
        # Create
        create_response = await integration_client.post(
            "/api/v1/items",
            json={"name": "Workflow Item", "price": 10.0},
        )
        assert create_response.status_code == 201
        item_id = create_response.json()["id"]

        # Update
        update_response = await integration_client.patch(
            f"/api/v1/items/{item_id}",
            json={"name": "Updated Item", "price": 15.0},
        )
        assert update_response.status_code == 200
        updated_item = update_response.json()
        assert updated_item["name"] == "Updated Item"
        assert updated_item["price"] == 15.0

        # Verify update
        get_response = await integration_client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Updated Item"

        # Delete
        delete_response = await integration_client.delete(f"/api/v1/items/{item_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_deleted_response = await integration_client.get(f"/api/v1/items/{item_id}")
        assert get_deleted_response.status_code == 404

    async def test_list_items_pagination(self, integration_client: AsyncClient):
        """Test listing items with pagination."""
        # Create multiple items
        for i in range(15):
            await integration_client.post(
                "/api/v1/items",
                json={"name": f"Item {i}", "price": float(i)},
            )

        # Test default pagination
        response = await integration_client.get("/api/v1/items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) <= 100

        # Test custom pagination
        response = await integration_client.get("/api/v1/items?skip=5&limit=5")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 5

    async def test_validation_errors(self, integration_client: AsyncClient):
        """Test API validation errors."""
        # Missing required field
        response = await integration_client.post(
            "/api/v1/items",
            json={"description": "Missing name and price"},
        )
        assert response.status_code == 422

        # Invalid price (must be > 0)
        response = await integration_client.post(
            "/api/v1/items",
            json={"name": "Invalid Price", "price": -10.0},
        )
        assert response.status_code == 422

    async def test_not_found_error(self, integration_client: AsyncClient):
        """Test 404 error for non-existent item."""
        response = await integration_client.get("/api/v1/items/99999")
        assert response.status_code == 404


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    async def test_health_endpoints_integration(self, integration_client: AsyncClient):
        """Test all health check endpoints."""
        # Health check
        response = await integration_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Readiness check
        response = await integration_client.get("/health/ready")
        assert response.status_code == 200

        # Liveness check
        response = await integration_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
