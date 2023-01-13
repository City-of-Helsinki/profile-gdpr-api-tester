from aiohttp import web

from .config import app_config

routes = web.RouteTableDef()


@routes.get("/{path:.*/?}.well-known/openid-configuration")
async def handle_openid_configuration(request):
    jwks_uri = (
        app_config.ISSUER
        + ("/" if not app_config.ISSUER.endswith("/") else "")
        + "jwks"
    )

    data = {
        "issuer": app_config.ISSUER,
        "jwks_uri": jwks_uri,
    }

    return web.json_response(data)


@routes.get("/{path:.*/?}jwks")
async def handle_jwks(request):
    from .rsa_key import kid, rsa_key

    key_data = rsa_key.public_key().to_dict()
    key_data.update(
        {
            "kid": kid,
        }
    )

    data = {"keys": [key_data]}

    return web.json_response(data)
