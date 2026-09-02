# ruff: noqa: I001
from fastapi.testclient import TestClient
from webapp import app


client = TestClient(app)


def test_health_endpoint_is_fast_and_does_not_initialize_rag():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "praxa-web"}


def test_home_exposes_webmcp_interface_and_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert "WebMCP Theatre Research" in response.text
    assert response.headers["origin-agent-cluster"] == "?1"
    assert response.headers["permissions-policy"] == "tools=(self)"


def test_client_registers_three_genuine_webmcp_tools():
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "document.modelContext.registerTool" in response.text
    assert 'name: "ask_theatre"' in response.text
    assert 'name: "search_theatre_archive"' in response.text
    assert 'name: "compare_productions"' in response.text
