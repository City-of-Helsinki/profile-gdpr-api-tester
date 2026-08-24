import asyncio
import json
import sys
from types import SimpleNamespace

import aiohttp
import pytest
from aiohttp import ContentTypeError

from gdpr_api_tester.config import IssuerType, app_config
from gdpr_api_tester.main import (
    STOP_EVENT,
    _handle_delete_command,
    _handle_query_command,
    _handle_set_command,
    _is_valid_gdpr_api_error,
    generate_api_token,
    get_delete_explanation,
    get_gdpr_url,
    get_query_explanation,
    is_valid_gdpr_api_errors,
    make_gdpr_api_request,
    read_command,
)


class _FakeResponse:
    def __init__(self, status: int, text_data: str = "", json_data: object = None):
        self.status = status
        self._text_data = text_data
        self._json_data = json_data

    async def text(self) -> str:
        return self._text_data

    async def json(self) -> object:
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class _FakeBuiltUrl:
    def __init__(self, url: str):
        self.url = url

    def update_query(self, params: dict[str, str] | None):
        if not params:
            return self.url
        items = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.url}?{items}"


class _FakeAiohttpResponse:
    def __init__(self):
        self.read_called = False

    async def read(self) -> bytes:
        self.read_called = True
        return b"{}"


class _FakeClientSession:
    def __init__(self, *, should_raise: Exception | None = None):
        self.should_raise = should_raise
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def _build_url(self, url: str) -> _FakeBuiltUrl:
        return _FakeBuiltUrl(url)

    async def get(self, url: str, params=None, ssl=False):
        self.calls.append(("get", {"url": url, "params": params, "ssl": ssl}))
        if self.should_raise:
            raise self.should_raise
        return _FakeAiohttpResponse()

    async def delete(self, url: str, params=None, ssl=False):
        self.calls.append(("delete", {"url": url, "params": params, "ssl": ssl}))
        if self.should_raise:
            raise self.should_raise
        return _FakeAiohttpResponse()


def test_get_gdpr_url_substitutes_template_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        app_config,
        "GDPR_API_URL",
        "http://example.test/gdpr/$user_uuid/$profile_id",
    )
    monkeypatch.setattr(app_config, "USER_UUID", "user-123")
    monkeypatch.setattr(app_config, "PROFILE_ID", "profile-456")

    assert get_gdpr_url() == "http://example.test/gdpr/user-123/profile-456"


def test_get_gdpr_url_appends_profile_id_without_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(app_config, "GDPR_API_URL", "http://example.test/gdpr/")
    monkeypatch.setattr(app_config, "USER_UUID", "user-123")
    monkeypatch.setattr(app_config, "PROFILE_ID", "profile-456")

    assert get_gdpr_url() == "http://example.test/gdpr/profile-456"


@pytest.mark.parametrize(
    "error",
    [
        {},
        {"code": "", "message": {"en": "msg"}},
        {"code": "bad", "message": "not-a-dict"},
        {"code": "bad", "message": {"en": 1}},
        {"code": "bad", "message": {"": "msg"}},
        {"code": "bad", "message": {"en": "msg"}, "extra": "field"},
    ],
)
def test_is_valid_gdpr_api_error_rejects_invalid_error_objects(error: object) -> None:
    assert _is_valid_gdpr_api_error(error) is False


def test_is_valid_gdpr_api_error_accepts_valid_error_object() -> None:
    assert _is_valid_gdpr_api_error({"code": "invalid_scope", "message": {"en": "Invalid scope"}}) is True


@pytest.mark.parametrize(
    "payload,expected",
    [
        (None, False),
        (["not-a-dict"], False),
        ({}, False),
        ({"errors": None}, False),
        ({"errors": "not-a-list"}, False),
        ({"errors": [{"code": "bad", "message": {"en": "Bad"}}]}, True),
        ({"errors": [{"message": {"en": "Bad"}}]}, False),
    ],
)
def test_is_valid_gdpr_api_errors_handles_various_payloads(
    payload: object,
    expected: bool,
) -> None:
    assert is_valid_gdpr_api_errors(payload) is expected


@pytest.mark.parametrize(
    "status,text_data,expected_snippets",
    [
        (200, json.dumps({"ok": True}), ["Success.", '"ok": true']),
        (200, "not-json", ["Failure.", "Raw content:"]),
        (400, json.dumps({"errors": []}), ["Parameters in the request failed validation", '"errors": []']),
        (418, "teapot", ["Unknown response status code", "teapot"]),
    ],
)
def test_get_query_explanation_formats_output(
    status: int,
    text_data: str,
    expected_snippets: list[str],
) -> None:
    response = _FakeResponse(status, text_data=text_data)

    explanation = asyncio.run(get_query_explanation(response))

    for snippet in expected_snippets:
        assert snippet in explanation


@pytest.mark.parametrize(
    "dry_run,expected_snippet",
    [
        (True, "can do the needed"),
        (False, "no longer contains personal data"),
    ],
)
def test_get_delete_explanation_204_variants(
    dry_run: bool,
    expected_snippet: str,
) -> None:
    explanation = asyncio.run(get_delete_explanation(_FakeResponse(204), dry_run=dry_run))

    assert "Success." in explanation
    assert expected_snippet in explanation


def test_get_delete_explanation_with_valid_errors_payload() -> None:
    payload = {"errors": [{"code": "denied", "message": {"en": "Deletion denied"}}]}
    response = _FakeResponse(403, json_data=payload)

    explanation = asyncio.run(get_delete_explanation(response))

    assert "(The errors are in the correct format)" in explanation
    assert '"code": "denied"' in explanation


def test_get_delete_explanation_with_invalid_errors_payload() -> None:
    payload = {"errors": [{"message": {"en": "Missing code"}}]}
    response = _FakeResponse(500, json_data=payload)

    explanation = asyncio.run(get_delete_explanation(response))

    assert "(The errors are NOT in the correct format)" in explanation


def test_get_delete_explanation_handles_non_json_error_content() -> None:
    response = _FakeResponse(500, json_data=ContentTypeError(None, None))

    explanation = asyncio.run(get_delete_explanation(response))

    assert "No content in response or JSON parsing failed." in explanation


def test_handle_set_command_without_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)

    asyncio.run(_handle_set_command(None))

    assert printed == ["set command needs arguments"]


def test_handle_set_command_with_valid_input(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    def fake_set_config(key: str, value: str) -> None:
        assert key == "USER_UUID"
        assert value == "abc-123"

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr(app_config, "set_config", fake_set_config)

    asyncio.run(_handle_set_command("USER_UUID=abc-123"))

    assert printed == ["Set config USER_UUID value to abc-123"]


def test_handle_query_command_prints_explanation(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    async def fake_request(method: str, scopes: list[str], params=None) -> _FakeResponse:
        assert method == "get"
        assert isinstance(scopes, list)
        return _FakeResponse(200, text_data=json.dumps({"ok": True}))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.make_gdpr_api_request", fake_request)

    asyncio.run(_handle_query_command())

    assert any("Success." in line for line in printed)


def test_handle_delete_command_uses_dry_run_param(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    async def fake_request(method: str, scopes: list[str], params=None) -> _FakeResponse:
        assert method == "delete"
        assert params == {"dry_run": "true"}
        return _FakeResponse(204)

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.make_gdpr_api_request", fake_request)

    asyncio.run(_handle_delete_command("dryrun"))

    assert any("Success." in line for line in printed)


def test_generate_api_token_without_scopes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_config, "ISSUER", "http://issuer")
    monkeypatch.setattr(app_config, "USER_UUID", "user-1")
    monkeypatch.setattr(app_config, "GDPR_API_AUDIENCE", "aud")
    monkeypatch.setattr(app_config, "SID", "sid-1")
    monkeypatch.setattr(app_config, "LOA", "low")

    fake_rsa_module = SimpleNamespace(kid="kid-1", rsa_key="fake-key")
    monkeypatch.setitem(sys.modules, "gdpr_api_tester.rsa_key", fake_rsa_module)

    captured: dict[str, object] = {}

    def fake_encode(claims: dict[str, object], key: object, algorithm: str, headers: dict[str, str]) -> str:
        captured["claims"] = claims
        captured["key"] = key
        captured["algorithm"] = algorithm
        captured["headers"] = headers
        return "token-1"

    monkeypatch.setattr("gdpr_api_tester.main.jwt.encode", fake_encode)

    token, claims = generate_api_token()

    assert token == "token-1"
    assert claims["iss"] == "http://issuer"
    assert captured["key"] == "fake-key"
    assert captured["headers"] == {"kid": "kid-1"}


def test_generate_api_token_with_tunnistamo_scopes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_config, "ISSUER", "http://issuer")
    monkeypatch.setattr(app_config, "USER_UUID", "user-1")
    monkeypatch.setattr(app_config, "GDPR_API_AUDIENCE", "aud")
    monkeypatch.setattr(app_config, "SID", "sid-1")
    monkeypatch.setattr(app_config, "LOA", "low")
    monkeypatch.setattr(app_config, "ISSUER_TYPE", IssuerType.TUNNISTAMO)
    monkeypatch.setattr(app_config, "GDPR_API_AUTHORIZATION_FIELD", "http://auth")

    fake_rsa_module = SimpleNamespace(kid="kid-2", rsa_key="fake-key")
    monkeypatch.setitem(sys.modules, "gdpr_api_tester.rsa_key", fake_rsa_module)
    monkeypatch.setattr("gdpr_api_tester.main.jwt.encode", lambda *args, **kwargs: "token-2")

    _, claims = generate_api_token(scopes=["example.scope"])

    assert claims["http://auth"] == ["example.scope"]


def test_generate_api_token_with_keycloak_scopes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_config, "ISSUER", "http://issuer")
    monkeypatch.setattr(app_config, "USER_UUID", "user-1")
    monkeypatch.setattr(app_config, "GDPR_API_AUDIENCE", "aud")
    monkeypatch.setattr(app_config, "SID", "sid-1")
    monkeypatch.setattr(app_config, "LOA", "low")
    monkeypatch.setattr(app_config, "ISSUER_TYPE", IssuerType.KEYCLOAK)

    fake_rsa_module = SimpleNamespace(kid="kid-3", rsa_key="fake-key")
    monkeypatch.setitem(sys.modules, "gdpr_api_tester.rsa_key", fake_rsa_module)
    monkeypatch.setattr("gdpr_api_tester.main.jwt.encode", lambda *args, **kwargs: "token-3")

    _, claims = generate_api_token(scopes=["example.gdprquery", "example.gdprdelete"])

    assert claims["authorization"] == {"permissions": [{"scopes": ["gdprquery", "gdprdelete"]}]}


def test_make_gdpr_api_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    session = _FakeClientSession()

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.get_gdpr_url", lambda: "http://api.test/gdpr")
    monkeypatch.setattr(
        "gdpr_api_tester.main.generate_api_token",
        lambda scopes=None: ("tok", {"sub": "user"}),
    )
    monkeypatch.setattr("gdpr_api_tester.main.ClientSession", lambda **kwargs: session)

    response = asyncio.run(make_gdpr_api_request("get", ["scope.read"], {"dry_run": "true"}))

    assert isinstance(response, _FakeAiohttpResponse)
    assert response.read_called is True
    assert any("GET http://api.test/gdpr?dry_run=true" in line for line in printed)


def test_make_gdpr_api_request_handles_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    session = _FakeClientSession(should_raise=aiohttp.ClientError("boom"))

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.get_gdpr_url", lambda: "http://api.test/gdpr")
    monkeypatch.setattr(
        "gdpr_api_tester.main.generate_api_token",
        lambda scopes=None: ("tok", {"sub": "user"}),
    )
    monkeypatch.setattr("gdpr_api_tester.main.ClientSession", lambda **kwargs: session)

    response = asyncio.run(make_gdpr_api_request("delete", ["scope.delete"]))

    assert response is None
    assert any("boom" in line for line in printed)


def test_make_gdpr_api_request_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    session = _FakeClientSession(should_raise=TimeoutError())

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.get_gdpr_url", lambda: "http://api.test/gdpr")
    monkeypatch.setattr(
        "gdpr_api_tester.main.generate_api_token",
        lambda scopes=None: ("tok", {"sub": "user"}),
    )
    monkeypatch.setattr("gdpr_api_tester.main.ClientSession", lambda **kwargs: session)

    response = asyncio.run(make_gdpr_api_request("get", ["scope.read"]))

    assert response is None
    assert any("The request timed out" in line for line in printed)


def test_handle_set_command_prints_error_when_set_config_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    def fake_set_config(key: str, value: str) -> None:
        raise ValueError("bad config")

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr(app_config, "set_config", fake_set_config)

    asyncio.run(_handle_set_command("USER_UUID=abc-123"))

    assert printed == ["bad config"]


def test_handle_set_command_ignores_unmatched_assignment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    printed: list[str] = []

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)

    asyncio.run(_handle_set_command("not an assignment"))

    assert printed == []


def test_read_command_handles_unknown_and_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    inputs = iter(["unknown", "exit"])
    STOP_EVENT.clear()

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    async def fake_ainput(prompt: str = "> ") -> str:
        return next(inputs)

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.ainput", fake_ainput)

    asyncio.run(read_command())

    assert any("Unknown command" in line for line in printed)
    assert STOP_EVENT.is_set() is True


def test_read_command_handles_eof(monkeypatch: pytest.MonkeyPatch) -> None:
    printed: list[str] = []
    STOP_EVENT.clear()

    async def fake_aprint(*args: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    async def fake_ainput(prompt: str = "> ") -> str:
        raise EOFError()

    monkeypatch.setattr("gdpr_api_tester.main.aprint", fake_aprint)
    monkeypatch.setattr("gdpr_api_tester.main.ainput", fake_ainput)

    asyncio.run(read_command())

    assert any("Exiting..." in line for line in printed)
    assert STOP_EVENT.is_set() is True
