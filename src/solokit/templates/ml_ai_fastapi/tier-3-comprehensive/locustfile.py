"""
Locust load testing configuration for FastAPI application
https://docs.locust.io/
"""

from locust import HttpUser, between, task  # type: ignore[import-not-found]

# HTTP status codes
HTTP_NOT_FOUND = 404


class FastAPIUser(HttpUser):
    """
    Simulated user for load testing the FastAPI application.
    """

    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)

    # Base host will be set via command line: locust --host=http://localhost:8000

    @task(3)
    def get_root(self) -> None:
        """Test the root endpoint (higher weight = 3)."""
        self.client.get("/")

    @task(5)
    def health_check(self) -> None:
        """Test the health check endpoint (higher weight = 5)."""
        self.client.get("/health")

    @task(2)
    def list_items(self) -> None:
        """Test listing items."""
        self.client.get("/api/v1/items")

    @task(1)
    def create_item(self) -> None:
        """Test creating an item."""
        self.client.post(
            "/api/v1/items",
            json={
                "name": "Load Test Item",
                "description": "Created during load testing",
                "price": 99.99,
            },
        )

    @task(1)
    def get_item(self) -> None:
        """Test getting a specific item."""
        # Note: This assumes item with ID 1 exists
        # In production, you'd create items first
        with self.client.get("/api/v1/items/1", catch_response=True) as response:
            if response.status_code == HTTP_NOT_FOUND:
                response.success()  # Mark as success even if not found

    def on_start(self) -> None:
        """
        Called when a simulated user starts.
        Use this to set up test data or authenticate.
        """
        # Example: Create test items
        for i in range(3):
            self.client.post(
                "/api/v1/items",
                json={
                    "name": f"Test Item {i}",
                    "description": f"Description {i}",
                    "price": 10.0 * (i + 1),
                },
            )

    def on_stop(self) -> None:
        """
        Called when a simulated user stops.
        Use this to clean up test data.
        """
        pass


class AdminUser(HttpUser):
    """
    Simulated admin user with different behavior patterns.
    """

    wait_time = between(2, 5)

    @task(1)
    def check_readiness(self) -> None:
        """Test the readiness check endpoint."""
        self.client.get("/health/ready")

    @task(1)
    def check_liveness(self) -> None:
        """Test the liveness check endpoint."""
        self.client.get("/health/live")


# Run with:
# locust --host=http://localhost:8000
# locust --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 1m
