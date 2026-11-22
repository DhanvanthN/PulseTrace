"""Regression tests for production Docker/nginx configuration."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_nginx_proxies_api_to_backend() -> None:
    conf = (REPO / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "location /api/" in conf
    assert "proxy_pass http://backend:8000" in conf
    assert "return 404" not in conf


def test_prod_qa_compose_has_isolated_volumes() -> None:
    text = (REPO / "docker-compose.prod.qa.yml").read_text(encoding="utf-8")
    assert "pgdata_qa" in text
    assert "uploads_qa" in text
    assert "container_name:" not in text
    assert "pulsetrace-postgres" not in text


def test_backend_compose_healthcheck() -> None:
    text = (REPO / "docker-compose.prod.qa.yml").read_text(encoding="utf-8")
    assert "health/database" in text
    assert "condition: service_healthy" in text