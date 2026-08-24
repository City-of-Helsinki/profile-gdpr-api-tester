import os

import pytest

_TEST_ENV_DEFAULTS = {
    "ISSUER": "http://localhost:8888/",
    "GDPR_API_AUDIENCE": "http://example.com/exampleapi",
    "GDPR_API_AUTHORIZATION_FIELD": "http://example.com",
    "GDPR_API_QUERY_SCOPE": "exampleapi.gdprquery",
    "GDPR_API_DELETE_SCOPE": "exampleapi.gdprdelete",
    "GDPR_API_URL": "http://localhost:8000/gdpr-api/v1/user/$user_uuid",
}

for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)


@pytest.fixture
def minimal_env() -> dict[str, str]:
    return dict(_TEST_ENV_DEFAULTS)
