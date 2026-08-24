import pytest

from gdpr_api_tester.config import AppConfig, IssuerType


def test_app_config_loads_required_fields(minimal_env: dict[str, str]) -> None:
    config = AppConfig(minimal_env)

    assert config.ISSUER == minimal_env["ISSUER"]
    assert config.GDPR_API_AUDIENCE == minimal_env["GDPR_API_AUDIENCE"]


def test_app_config_uses_default_issuer_type(minimal_env: dict[str, str]) -> None:
    config = AppConfig(minimal_env)

    assert config.ISSUER_TYPE == IssuerType.TUNNISTAMO


def test_app_config_requires_mandatory_values(minimal_env: dict[str, str]) -> None:
    env_without_issuer = dict(minimal_env)
    env_without_issuer.pop("ISSUER")

    with pytest.raises(RuntimeError, match='The configuration field "ISSUER" is required'):
        AppConfig(env_without_issuer)


def test_app_config_rejects_unknown_key(minimal_env: dict[str, str]) -> None:
    config = AppConfig(minimal_env)

    with pytest.raises(ValueError):
        config.set_config("UNKNOWN_KEY", "value")


def test_app_config_string_representation_contains_keys(
    minimal_env: dict[str, str],
) -> None:
    config = AppConfig(minimal_env)

    result = str(config)

    assert result.startswith("Configuration:\n")
    assert "ISSUER = http://localhost:8888/" in result
    assert "GDPR_API_AUDIENCE = http://example.com/exampleapi" in result
