"""
Standaard contract tests die voor ELKE service moeten slagen.
De Builder kopieert dit als tests/test_template_contract.py in elke service.
"""
import pytest


@pytest.mark.contract
def test_health_endpoint_returns_ok(client):
    """Liveness probe moet altijd snel '200 OK' geven."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.contract
def test_ready_endpoint_returns_status(client):
    """Readiness probe moet 200 of 503 met 'checks' veld geven."""
    r = client.get("/ready")
    assert r.status_code in (200, 503)
    body = r.json()
    assert "status" in body
    assert "checks" in body


@pytest.mark.contract
def test_metrics_endpoint_returns_prometheus_format(client):
    """Metrics endpoint moet Prometheus exposition format leveren."""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    text = r.text
    # Prometheus exposition format heeft '# HELP' regels
    assert "# HELP" in text or "# TYPE" in text


@pytest.mark.contract
def test_request_id_header_set(client):
    """Elke response moet X-Request-ID header bevatten."""
    r = client.get("/health")
    assert "x-request-id" in {k.lower() for k in r.headers.keys()}


@pytest.mark.contract
def test_security_headers_present(client):
    """Standaard security headers moeten gezet zijn."""
    r = client.get("/health")
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert headers_lower.get("x-content-type-options") == "nosniff"
    assert headers_lower.get("x-frame-options") == "DENY"


@pytest.mark.contract
def test_openapi_spec_available(client):
    """OpenAPI spec moet bereikbaar en valide JSON zijn."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "openapi" in spec
    assert "paths" in spec
    assert "/health" in spec["paths"]
    assert "/ready" in spec["paths"]
