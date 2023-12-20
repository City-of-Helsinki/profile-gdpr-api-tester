import asyncio
import json
import re
import time
import urllib.parse
from json import JSONDecodeError
from string import Template

import aiohttp
from aioconsole import ainput, aprint
from aiohttp import ClientSession, ContentTypeError, web
from colorama import Fore, Style, just_fix_windows_console
from jose import jwt
from jose.constants import ALGORITHMS

from .config import app_config, IssuerType
from .routes import routes

HELP_TEXT = """
Commands:

 help - This help
 config - Show configuration
 keys - Print public and private keys used in the OIDC Simulator
 set - Set configuration value e.g. set USER_UUID=0000-000...
 query - Make GDPR query request to the API
 delete - Make GDPR delete request to the API
 delete dryrun - Make GDPR delete dry-run request to the API
 exit - Quit the GDPR API Tester
"""

# An event used to exit the tester
STOP_EVENT = asyncio.Event()


def get_gdpr_url() -> str:
    """Constructs and returns the GDPR URL

    Constructs the GDPR URL the same way the Profile Back end constructs it.
    """
    url_template = Template(app_config.GDPR_API_URL)
    mapping = {
        "profile_id": app_config.PROFILE_ID,
        "user_uuid": app_config.USER_UUID,
    }

    gdpr_url = url_template.safe_substitute(mapping)

    if gdpr_url == app_config.GDPR_API_URL:
        return urllib.parse.urljoin(app_config.GDPR_API_URL, app_config.PROFILE_ID)

    return gdpr_url


def generate_api_token(scopes=None):
    from .rsa_key import kid, rsa_key

    now = int(time.time())
    claims = {
        "iss": app_config.ISSUER,
        "sub": app_config.USER_UUID,
        "aud": app_config.GDPR_API_AUDIENCE,
        "exp": now + 300,
        "iat": now - 300,
        "auth_time": now - 300,
        "sid": app_config.SID,
        "loa": app_config.LOA,
    }
    if scopes:
        match app_config.ISSUER_TYPE:
            case IssuerType.TUNNISTAMO:
                claims[app_config.GDPR_API_AUTHORIZATION_FIELD] = scopes
            case IssuerType.KEYCLOAK:
                kc_scopes = [s.rsplit(".", 1)[-1] for s in scopes]
                claims["authorization"] = {
                    "permissions": [
                        {
                            "scopes": [
                                kc_scopes
                            ]
                        }
                    ]
                }

    token = jwt.encode(
        claims, key=rsa_key, algorithm=ALGORITHMS.RS256, headers={"kid": kid}
    )

    return token, claims


COMMON_RESPONSE_CODE_EXPLANATION = {
    400: Fore.RED
    + "Failure. "
    + Style.RESET_ALL
    + "Parameters in the request failed validation",
    401: Fore.RED
    + "Failure. "
    + Style.RESET_ALL
    + "Credentials in the request were missing or were invalid.",
    404: Fore.RED
    + "Failure. "
    + Style.RESET_ALL
    + "GDPR API not found. Misconfigured?",
    500: Fore.RED
    + "Failure. "
    + Style.RESET_ALL
    + "There has been an unexpected error.\n\n"
    + "The error(s) may be detailed in the response:",
}


def is_valid_gdpr_api_errors(response_json):
    if not response_json:
        return False

    try:
        errors = response_json.get("errors")
    except AttributeError:
        return False

    try:
        iter(errors)
    except TypeError:
        return False

    expected_keys = {"code", "message"}
    for error in errors:
        if set(error.keys()) != expected_keys:
            return False
        if not error.get("code") or not isinstance(error["code"], str):
            return False
        if not error.get("message") or not isinstance(error["message"], dict):
            return False

        for key, value in error["message"].items():
            if not key or not isinstance(value, str):
                return False

    return True


async def get_query_explanation(response):
    QUERY_RESPONSE_CODE_EXPLANATION = COMMON_RESPONSE_CODE_EXPLANATION.copy()
    QUERY_RESPONSE_CODE_EXPLANATION.update({
        204: Fore.GREEN
        + "Success. There is no personal data related to the profile.\n"
        + Style.RESET_ALL,
    })

    explanation = (
        f"Response status code: {response.status}\n"
        f"How the Profile back-end would interpret the response:\n\n"
    )

    response_content = await response.text()

    response_json_string = ""
    try:
        response_json = json.loads(response_content)
        response_json_string = json.dumps(response_json, indent=4)
    except JSONDecodeError:
        pass

    if response.status == 200:
        if response_json_string:
            explanation += Fore.GREEN + "Success.\n" + Style.RESET_ALL
            explanation += "The response JSON:\n" + Style.RESET_ALL
            explanation += response_json_string
        else:
            explanation += Fore.RED + "Failure.\n" + Style.RESET_ALL
            explanation += (
                "No content in response or JSON parsing failed. Raw content:\n"
            )
            explanation += response_content
    else:
        if response.status in QUERY_RESPONSE_CODE_EXPLANATION:
            explanation += QUERY_RESPONSE_CODE_EXPLANATION[response.status] + "\n"
        else:
            explanation += Fore.RED + "Unknown response status code\n" + Style.RESET_ALL

        if response_json_string:
            explanation += response_json_string
        else:
            explanation += (
                "No content in response or JSON parsing failed. Raw content:\n"
            )
            explanation += response_content

    return explanation


async def get_delete_explanation(response, dry_run=False):
    DELETE_RESPONSE_CODE_EXPLANATION = COMMON_RESPONSE_CODE_EXPLANATION.copy()
    DELETE_RESPONSE_CODE_EXPLANATION.update({
        403: Fore.YELLOW
        + "Deletion denied. "
        + Style.RESET_ALL
        + "Data can not be removed from the service.\n\n"
        + "The reason(s) for the failure may be detailed in the response:",
    })

    explanation = (
        f"Response status code: {response.status}\n"
        f"How the Profile back-end would interpret the response:\n\n"
    )

    if response.status == 204:
        if not dry_run:
            explanation += (
                Fore.GREEN
                + "Success. The service no longer contains personal data for the profile.\n"
                + Style.RESET_ALL
            )
        else:
            explanation += (
                Fore.GREEN
                + "Success. "
                + "The service can do the needed so that it would no longer contain personal data for the profile.\n"
                + Style.RESET_ALL
            )

        return explanation

    if response.status in DELETE_RESPONSE_CODE_EXPLANATION:
        explanation += DELETE_RESPONSE_CODE_EXPLANATION[response.status] + "\n"
    else:
        explanation += "Unknown response status code\n"

    if response.status in [403, 500]:
        response_json_string = ""
        try:
            response_json = await response.json()
            if is_valid_gdpr_api_errors(response_json):
                explanation += (
                    Fore.GREEN
                    + "(The errors are in the correct format)\n"
                    + Style.RESET_ALL
                )
            else:
                explanation += (
                    Fore.RED
                    + "(The errors are NOT in the correct format)\n"
                    + Style.RESET_ALL
                )

            response_json_string = json.dumps(response_json, indent=4)
        except ContentTypeError:
            pass

        if response_json_string:
            explanation += response_json_string
        else:
            explanation += "No content in response or JSON parsing failed.\n"

    return explanation


async def make_gdpr_api_request(method, scopes, params=None):
    url = get_gdpr_url()
    (token, claims) = generate_api_token(scopes=scopes)
    authorization = "Bearer " + token

    headers = {"Authorization": authorization}
    async with ClientSession(
        headers=headers, timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        final_url = session._build_url(url).update_query(params)

        await aprint("\nSending GDPR API request")
        await aprint(f"{method.upper()} {final_url}")
        await aprint(f"Authorization header:\n\n{authorization}\n")
        await aprint(f"Token claims:\n\n{json.dumps(claims, indent=4)}\n")

        try:
            response = await getattr(session, method)(url, params=params, ssl=False)
            # Make the aiohttp read the response payload and save it to the instance
            await response.read()
            return response
        except aiohttp.ClientError as e:
            await aprint(e)
        except asyncio.TimeoutError:
            await aprint("The request timed out")


async def read_command():
    await aprint(HELP_TEXT)

    while True:
        try:
            line = await ainput(prompt="> ")
        except EOFError:
            await aprint("Exiting...")
            STOP_EVENT.set()
            return

        parts = line.strip().split(" ", 1)
        command = parts[0].strip()
        arguments = None
        if len(parts) > 1:
            arguments = parts[1].strip()

        if command == "help":
            await aprint(HELP_TEXT)
        elif command == "config":
            await aprint(app_config)
        elif command == "keys":
            from .rsa_key import rsa_key

            await aprint(rsa_key.public_key().to_pem("PKCS1").decode())
            await aprint(rsa_key.to_pem("PKCS1").decode())
        elif command == "query":
            response = await make_gdpr_api_request(
                "get", [app_config.GDPR_API_QUERY_SCOPE]
            )
            if response:
                await aprint(await get_query_explanation(response))
        elif command == "delete":
            dry_run = arguments and "dryrun" in arguments
            params = {}
            if dry_run:
                params["dry_run"] = "true"
            response = await make_gdpr_api_request(
                "delete", [app_config.GDPR_API_DELETE_SCOPE], params
            )
            if response:
                await aprint(await get_delete_explanation(response, dry_run=dry_run))
        elif command == "exit" or line == "quit":
            await aprint("Exiting...")
            STOP_EVENT.set()
            return
        elif command == "set":
            if arguments:
                matches = re.match(r"(?P<key>\w+)\s*=\s*(?P<value>.*)", arguments)
                if matches:
                    try:
                        app_config.set_config(matches["key"], matches["value"])
                        await aprint(
                            "Set config", matches["key"], "value to", matches["value"]
                        )
                    except Exception as e:
                        await aprint(str(e))
            else:
                await aprint("set command needs arguments")
        else:
            await aprint(f'Unknown command "{line}". Use "help" for commands.')


async def run():
    """Coroutine that runs the OIDC simulator and the command prompt"""
    # Initialize aiohttp Application
    app = web.Application()
    app.add_routes(routes)

    # Run the aiohttp Application as a TCP server listening on port 8888
    # We are not using the aiohttp.web.run_app method because that is blocking, and we
    # want to also run the command prompt. See aiohttp docs for more information:
    # https://docs.aiohttp.org/en/stable/web_advanced.html#application-runners
    await aprint("Starting OIDC simulator")
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, port=8888).start()

    await aprint("Starting command prompt")
    asyncio.create_task(read_command())

    # Wait here until the STOP_EVENT event is set. The event is used to quit the tester.
    await STOP_EVENT.wait()

    await runner.cleanup()


def main():
    """The main entry point of the tester"""
    # The following command makes ANSI escapes to work on Windows
    # TODO: Untested
    just_fix_windows_console()
    print("GDPR API Tester v0.0.1\n")
    print(app_config, flush=True)

    # The following import is done here to generate the RSA key only when the tool
    # is run and not when this module is imported
    from .rsa_key import rsa_key  # NOQA: F401 imported but unused

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        # Catch the KeyboardInterrupt exception if the user quits the tester by using
        # CTRL-C key combination. There is no need to show the stack trace in that case.
        pass
