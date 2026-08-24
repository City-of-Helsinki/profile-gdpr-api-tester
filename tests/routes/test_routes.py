import asyncio
import json
import sys
from types import SimpleNamespace

from gdpr_api_tester import routes


def test_openid_configuration_uses_issuer_without_duplicate_slash(monkeypatch):
    monkeypatch.setattr(routes.app_config, "ISSUER", "http://localhost:8888")

    response = asyncio.run(routes.handle_openid_configuration(None))
    payload = json.loads(response.text)

    assert payload["issuer"] == "http://localhost:8888"
    assert payload["jwks_uri"] == "http://localhost:8888/jwks"
    assert "authorization_endpoint" in payload
    assert payload["subject_types_supported"] == ["public"]


def test_openid_configuration_keeps_existing_issuer_trailing_slash(monkeypatch):
    monkeypatch.setattr(routes.app_config, "ISSUER", "http://localhost:8888/")

    response = asyncio.run(routes.handle_openid_configuration(None))
    payload = json.loads(response.text)

    assert payload["jwks_uri"] == "http://localhost:8888/jwks"


def test_jwks_includes_kid_and_public_key(monkeypatch):
    class _FakePublicKey:
        def to_dict(self):
            return {"kty": "RSA", "n": "abc", "e": "AQAB"}

    class _FakeRsaKey:
        def public_key(self):
            return _FakePublicKey()

    fake_rsa_module = SimpleNamespace(kid="test-kid", rsa_key=_FakeRsaKey())
    monkeypatch.setitem(sys.modules, "gdpr_api_tester.rsa_key", fake_rsa_module)

    response = asyncio.run(routes.handle_jwks(None))
    payload = json.loads(response.text)

    assert payload["keys"]
    assert payload["keys"][0]["kid"] == "test-kid"
    assert payload["keys"][0]["kty"] == "RSA"
