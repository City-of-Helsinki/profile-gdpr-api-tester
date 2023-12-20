import os

from enum import Enum

from dotenv import find_dotenv, load_dotenv

class IssuerType(Enum):
    TUNNISTAMO = "tunnistamo"
    KEYCLOAK = "keycloak"

    def __str__(self) -> str:
        return self.value


# Find the dotenv path by using the current directory
#
# By default, dotenv would try to find the .env file from the same directory where this
# file is located which wouldn't work if the gdpr_api_tester package is in a virtualenv
# or such.
load_dotenv(dotenv_path=find_dotenv(usecwd=True))


class AppConfig:
    """Simple class for holding configuration values with support for a default value"""
    # The issuer in the generated API tokens and the address of the GDPR API Tester
    #   e.g. http://127.0.0.1:8888/
    #   The API must have connectivity to this address because the JWT token
    #   verification will fetch the public key from here.
    ISSUER: str

    # The type of the issuer (authorizaton server) that the GDPR API Tester simulates.
    # The type affects the contents of the generated access tokens.
    # Allowed values are "tunnistamo" and "keycloak".
    ISSUER_TYPE: IssuerType = IssuerType.TUNNISTAMO

    # The audience in the generated API tokens and the client id of the GDPR API
    #   e.g. http://localhost:8080/exampleapi
    GDPR_API_AUDIENCE: str

    # The field in the API tokens that contains the API scopes
    #   e.g. http://localhost:8080
    GDPR_API_AUTHORIZATION_FIELD: str

    # The GDPR query scope
    #   e.g. exampleapi.gdprquery
    # When issuer type is Keycloak, only the part after the last dot is used.
    # This makes for example the value `exampleapi.gdprquery` work
    # correctly in every case.
    GDPR_API_QUERY_SCOPE: str

    # The GDPR delete scope
    #   e.g. exampleapi.gdprdelete
    # When issuer type is Keycloak, only the part after the last dot is used.
    # This makes for example the value `exampleapi.gdprdelete` work
    # correctly in every case.
    GDPR_API_DELETE_SCOPE: str

    # The address of the GDPR API
    #   e.g. http://localhost:8050/gdpr-api/v1/user/$user_uuid
    #   The string "$profile_id" will be substituted with the value of PROFILE_ID.
    #   The string "$user_uuid" will be substituted with the value of USER_UUID.
    #   If there are no substitutions, the PROFILE_ID will be appended to the URL.
    GDPR_API_URL: str

    # The value which will replace the string "$profile_id" in the GDPR_API_URL
    #   e.g. 65d4015d-1736-4848-9466-25d43a1fe8c7
    PROFILE_ID: str = ""

    # The value for the "sub" claim in the generated API tokens and the value which
    # will replace the string "$user_uuid" in the GDPR_API_URL
    #   e.g. 9e14df7c-81f6-4c41-8578-6aa7b9d0e5c0
    USER_UUID: str = ""

    # The value for the "loa" (Level of assurance) claim in the generated API tokens
    #   e.g. "substantial" or "low"
    LOA: str = "substantial"

    # The value for the "sid" (Session ID) claim in the generated API tokens
    SID: str = "00000000-0000-4000-9000-000000000001"

    def get_keys(self):
        return [field for field in self.__annotations__ if field.isupper()]

    def __init__(self, env):
        for field in self.get_keys():
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise RuntimeError(
                    "The configuration field \"{}\" is required".format(field)
                )

            self.set_config(field, env.get(field, default_value))

    def set_config(self, name, value):
        if name not in self.get_keys():
            raise ValueError('Unknown config key: "{}"'.format(name))

        typ = self.__annotations__[name]

        self.__setattr__(name, typ(value))

    def __str__(self):
        result = "Configuration:\n"
        for field in self.get_keys():
            result += f"  {field} = {getattr(self, field)}\n"

        return result


# app_config is effectively a singleton as Python doesn't run the code multiple
# times when importing.
app_config = AppConfig(os.environ)
