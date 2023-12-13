from aiohttp import web

from .config import app_config

routes = web.RouteTableDef()


@routes.get("/{path:.*/?}.well-known/openid-configuration")
async def handle_openid_configuration(request):
    """OpenID configuration view

    The path part in the route is not used. It's just added to make the route
    match everything that ends in ".well-known/openid-configuration" to support
    ISSUER values with path parts.

    Only issuer and jwks_uri configuration values are necessary for validating
    the tokens, but authorization_endpoint, response_types_supported,
    subject_types_supported and id_token_signing_alg_values_supported are
    required by the spec.
    """
    jwks_uri = (
        app_config.ISSUER
        + ("/" if not app_config.ISSUER.endswith("/") else "")
        + "jwks"
    )

    data = {
        "issuer": app_config.ISSUER,
        "authorization_endpoint": "https://localhost/openid/authorize",
        "jwks_uri": jwks_uri,
        "response_types_supported": [
            "code",
            "id_token",
            "id_token token",
            "code token",
            "code id_token",
            "code id_token token",
        ],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256", "RS256"],
    }

    return web.json_response(data)


@routes.get("/{path:.*/?}jwks")
async def handle_jwks(request):
    """JSON Web Key Set view

    The path part in the route is not used. It's just added to make the route
    match everything that ends in "jwks" to support ISSUER values with path parts."""
    from .rsa_key import kid, rsa_key

    key_data = rsa_key.public_key().to_dict()
    # Add key id manually as RSAKey doesn't support key ids
    key_data.update(
        {
            "kid": kid,
        }
    )

    data = {"keys": [key_data]}

    return web.json_response(data)
