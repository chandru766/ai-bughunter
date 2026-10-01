import pytest
import os
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app
from scope.validator import ScopeValidator, ScopeDecision
from auth_bank.crypto import CryptoService

def test_security_headers():
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Content-Security-Policy") == "default-src 'self'"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"

def test_scope_validator_scheme_restriction():
    validator = ScopeValidator()
    validator.add_rule("example.com")
    
    # Allowed schemes
    assert validator.evaluate("http://example.com") == ScopeDecision.IN_SCOPE
    assert validator.evaluate("https://example.com") == ScopeDecision.IN_SCOPE
    
    # Blocked schemes
    assert validator.evaluate("ftp://example.com") == ScopeDecision.OUT_OF_SCOPE
    assert validator.evaluate("file:///etc/passwd") == ScopeDecision.OUT_OF_SCOPE
    assert validator.evaluate("gopher://example.com") == ScopeDecision.OUT_OF_SCOPE

def test_crypto_service_production_enforcement(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("AUTH_BANK_ENCRYPTION_KEY", raising=False)
    
    with pytest.raises(ValueError, match="AUTH_BANK_ENCRYPTION_KEY environment variable is required in production"):
        CryptoService.get_key()

def test_health_endpoints():
    client = TestClient(app)
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "alive"}
    
    res = client.get("/health/ready")
    # Will be 200 if DB is up
    assert res.status_code in [200, 503]
