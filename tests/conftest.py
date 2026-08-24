import pytest


@pytest.fixture
def minimal_env() -> dict[str, str]:
    return {
        "ISSUER": "http://localhost:8888/",
        "GDPR_API_AUDIENCE": "http://example.com/exampleapi",
        "GDPR_API_AUTHORIZATION_FIELD": "http://example.com",
        "GDPR_API_QUERY_SCOPE": "exampleapi.gdprquery",
        "GDPR_API_DELETE_SCOPE": "exampleapi.gdprdelete",
        "GDPR_API_URL": "http://localhost:8000/gdpr-api/v1/user/$user_uuid",
    }
