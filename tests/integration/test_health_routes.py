"""
tests/integration/test_health_routes.py

Health endpoint tests.

These seem trivial but are important:
- In Kubernetes, if /health/ready returns wrong status, pods get restarted
- If /health/live returns 500, your load balancer pulls the pod
- Never skip testing your health checks just because they "look simple"
"""


class TestHealthReady:
    def test_returns_200(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_returns_ok_status(self, client):
        """k8s readiness probe depends on this exact shape."""
        response = client.get("/health/ready")
        assert response.json() == {"status": "ok"}

    def test_content_type_is_json(self, client):
        response = client.get("/health/ready")
        assert "application/json" in response.headers["content-type"]

    def test_method_not_allowed_for_post(self, client):
        """Health endpoints should be GET-only."""
        response = client.post("/health/ready")
        assert response.status_code == 405


class TestHealthLive:
    def test_returns_200(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_returns_ok_status(self, client):
        response = client.get("/health/live")
        assert response.json() == {"status": "ok"}
