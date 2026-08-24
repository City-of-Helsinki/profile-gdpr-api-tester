import importlib
import sys

import rsa
from jose import jwk


def _import_fresh_rsa_key_module(monkeypatch, request, tmp_path, *, fake_newkeys, fake_construct):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(rsa, "newkeys", fake_newkeys)
    monkeypatch.setattr(jwk, "construct", fake_construct)
    
    # Save original module state and register cleanup for restoration
    original_module = sys.modules.pop("gdpr_api_tester.rsa_key", None)
    
    def restore_module():
        if original_module is not None:
            sys.modules["gdpr_api_tester.rsa_key"] = original_module
        else:
            sys.modules.pop("gdpr_api_tester.rsa_key", None)
    
    request.addfinalizer(restore_module)
    
    return importlib.import_module("gdpr_api_tester.rsa_key")


class _FakePrivateKey:
    def save_pkcs1(self):
        return b"private-key-bytes"


def _make_construct_spy():
    marker = object()
    calls = []

    def fake_construct(value, algorithm):
        calls.append((value, algorithm))
        return marker

    return marker, calls, fake_construct


def test_rsa_key_loads_existing_pem_file(monkeypatch, request, tmp_path):
    pem_path = tmp_path / "gdpr_api_tester_key.pem"
    pem_path.write_text("existing-pem")

    marker, calls, fake_construct = _make_construct_spy()

    def fake_newkeys(_bits):
        raise AssertionError("new key generation should not happen when PEM exists")

    module = _import_fresh_rsa_key_module(
        monkeypatch,
        request,
        tmp_path,
        fake_newkeys=fake_newkeys,
        fake_construct=fake_construct,
    )

    assert module.rsa_key is marker
    assert module.kid == "gdpr-api-tester-key"
    assert calls[0][0] == "existing-pem"


def test_rsa_key_generates_and_writes_new_key_when_missing(monkeypatch, request, tmp_path):
    marker, construct_calls, fake_construct = _make_construct_spy()
    fake_private_key = _FakePrivateKey()

    def fake_newkeys(bits):
        assert bits == 2048
        return object(), fake_private_key

    module = _import_fresh_rsa_key_module(
        monkeypatch,
        request,
        tmp_path,
        fake_newkeys=fake_newkeys,
        fake_construct=fake_construct,
    )

    assert module.rsa_key is marker
    assert construct_calls[0][0] is fake_private_key
    assert (tmp_path / "gdpr_api_tester_key.pem").read_bytes() == b"private-key-bytes"


def test_rsa_key_handles_read_permission_error(monkeypatch, request, tmp_path):
    marker, construct_calls, fake_construct = _make_construct_spy()
    fake_private_key = _FakePrivateKey()
    real_open = open

    def fake_newkeys(_bits):
        return object(), fake_private_key

    def fake_open(path, mode="r", *args, **kwargs):
        if path == "gdpr_api_tester_key.pem" and mode == "r":
            raise PermissionError()
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)

    module = _import_fresh_rsa_key_module(
        monkeypatch,
        request,
        tmp_path,
        fake_newkeys=fake_newkeys,
        fake_construct=fake_construct,
    )

    assert module.rsa_key is marker
    assert construct_calls[0][0] is fake_private_key
