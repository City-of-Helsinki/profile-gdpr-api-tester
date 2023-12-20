Helsinki Profile GDPR API Tester
================================

Profile GDPR API Tester is a command line tool for testing GDPR API implementations that conform to the Helsinki Profile GDPR API specification.
This tools main usage is to test the API Token authentication in the implemented GDPR API.

See [GDPR API Description](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/KAN/pages/80969736/GDPR+API+Description) for more information about the GDPR API.

# Requirements

Python 3.10+ or Docker

# Installing / Running

## Running from a GitHub package using Docker

Copy [env.example](env.example) to your local filesystem as `.env` and change the settings to suit your environment. (See [configuration](#configuration))

```shell
docker run -i -p 8888:8888 --env-file .env ghcr.io/city-of-helsinki/profile-gdpr-api-tester
```


## Installing using pip

You can install this tool in your local Python environment by running

```shell
pip install gdpr-api-tester
```

## Running after installing with pip

Copy [env.example](env.example) to `.env` and change the settings to suit your environment. (See [configuration](#configuration))

Then run the command:

```shell
gdpr_api_tester
```

## Building and running using Docker

Clone this repository

```shell
git clone https://github.com/City-of-Helsinki/profile-gdpr-api-tester
cd profile-gdpr-api-tester
```

Copy [env.example](env.example) to `.env` and change the settings to suit your environment. (See [configuration](#configuration))

```shell
cp env.example .env
$EDITOR .env
```

Then build and run a Docker image:

```shell
docker build -t gdpr-api-tester .
docker run -i -p 8888:8888 --env-file .env gdpr-api-tester
```


## Running from this repo

```shell
git clone https://github.com/City-of-Helsinki/profile-gdpr-api-tester
cd profile-gdpr-api-tester
cp env.example .env
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m gdpr_api_tester
```

# Configuration

The tool reads configuration from environment variables and from a file named `.env`. There is an example env file ([env.example](env.example)) in the repository. You can use it as a base for your own configuration.

Following is a list of all the configuration options:

### ISSUER

The issuer in the generated API tokens and the address of the GDPR API Tester. The API must have connectivity to this address because the JWT token verification will fetch the public key from here.

### ISSUER_TYPE

The type of the issuer (authorizaton server) that the GDPR API Tester simulates. The type affects the contents of the generated access tokens. Allowed values are "tunnistamo" and "keycloak".

### GDPR_API_AUDIENCE

The audience in the generated API tokens. i.e. The client id of the GDPR API.

### GDPR_API_AUTHORIZATION_FIELD

The field in the API tokens that contains the API scopes. With Tunnistamo this is usually `https://api.hel.fi/auth`.
When using the tester this can be anything as long as the corresponding setting in the GDPR API is the same.

### GDPR_API_QUERY_SCOPE and GDPR_API_DELETE_SCOPE

The GDPR query and delete scopes. These are provided to the API developers by the Profile-team. The value is usually
`[GDPR_API_AUDIENCE].gdprquery` and `[GDPR_API_AUDIENCE].gdprdelete`. e.g. `http://localhost:8080/exampleapi.gdprdelete`.
But in the tool and [helsinki-profile-gdpr-api](https://github.com/City-of-Helsinki/helsinki-profile-gdpr-api) configurations the values must be configured without the domain part. In this example they would be `exampleapi.gdprquery` and `exampleapi.gdprdelete`.

### GDPR_API_URL

The address of the GDPR API. The string `$profile_id` will be substituted with the value of **PROFILE_ID**. The string `$user_uuid` will be substituted with the value of **USER_UUID**. If there are no substitutions, the **PROFILE_ID will** be appended to the URL.

### PROFILE_ID

The value which will replace the string `$profile_id` in the **GDPR_API_URL**.

### USER_UUID

The value for the "sub" claim in the generated API tokens and the value which will replace the string `$user_uuid` in the **GDPR_API_URL**.

### LOA

The value for the "loa" (Level of assurance) claim in the generated API tokens. Possible values are `substantial` and `low`. See the [GDPR API Description](https://helsinkisolutionoffice.atlassian.net/wiki/spaces/KAN/pages/80969736/GDPR+API+Description#The-effect-of-authentication-level) for more information.

### SID

The value for the "sid" (Session ID) claim in the generated API tokens. The GDPR API doesn't need to use the session id,
but it's included for completeness' sake.

# Usage

The tool starts as an interactive prompt the user can use to run commands.

> Commands:
>
>  help - This help\
>  config - Show configuration\
>  keys - Print public and private keys used in the OIDC Simulator\
>  set - Set configuration value e.g. set USER_UUID=0000-000...\
>  query - Make GDPR query request to the API\
>  delete - Make GDPR delete request to the API\
>  delete dryrun - Make GDPR delete dry-run request to the API\
>  exit - Quit the GDPR API Tester

## Full example with Docker

### Example backend

Clone the [Example backend](https://github.com/City-of-Helsinki/example-backend-profile/) repository and copy the example env file to config.env.

```shell
git clone https://github.com/City-of-Helsinki/example-backend-profile/
cd example-backend-profile
cp config.env.example config.env
```

Edit the example backend configuration file (config.env) and set the following values:

**Notice!** You must not use quotes around the values

    ALLOWED_HOSTS=host.docker.internal
    OIDC_AUDIENCE=http://example.com/exampleapi
    OIDC_API_AUTHORIZATION_FIELD=http://example.com
    OIDC_ISSUER=http://host.docker.internal:8888
    GDPR_API_QUERY_SCOPE=exampleapi.gdprquery
    GDPR_API_DELETE_SCOPE=exampleapi.gdprdelete

Build and start the example backend

```shell
docker build -t example-backend .
docker run -it -p 8000:8000 --env-file config.env example-backend
```

### GDPR API Tester

See the [Running using Docker](#running-using-docker) section and set the following values in the configuration:

    ISSUER=http://host.docker.internal:8888/
    GDPR_API_AUDIENCE=http://example.com/exampleapi
    GDPR_API_AUTHORIZATION_FIELD=http://example.com
    GDPR_API_QUERY_SCOPE=exampleapi.gdprquery
    GDPR_API_DELETE_SCOPE=exampleapi.gdprdelete
    GDPR_API_URL=http://host.docker.internal:8000/gdpr-api/v1/user/$user_uuid
    PROFILE_ID=65d4015d-1736-4848-9466-25d43a1fe8c7
    USER_UUID=9e14df7c-81f6-4c41-8578-6aa7b9d0e5c0
    LOA=substantial
    SID=00000000-0000-4000-9000-000000000001

You should be able to send requests to the example backend after the GDPR API Tester starts. e.g. issuing the "query" command should yield something like this:

```
> query

Sending GDPR API request
GET http://host.docker.internal:8000/gdpr-api/v1/user/9e14df7c-81f6-4c41-8578-6aa7b9d0e5c0
Authorization header:

Bearer eyJhbG...QTQNBYW_A

Token claims:

{
    "iss": "http://host.docker.internal:8888/",
    "sub": "9e14df7c-81f6-4c41-8578-6aa7b9d0e5c0",
    "aud": "http://example.com/exampleapi",
    "exp": 1673519671,
    "iat": 1673519071,
    "auth_time": 1673519071,
    "sid": "00000000-0000-4000-9000-000000000001",
    "loa": "substantial",
    "http://example.com": [
        "exampleapi.gdprquery"
    ]
}

Response status code: 200
How the Profile back-end would interpret the response:

Success.
The response JSON:
{
    "key": "EXAMPLE_DATA",
    "children": [
        {
            "key": "USER",
            "children": [
                {
                    "key": "FIRST_NAME",
                    "value": ""
                },
                {
                    "key": "LAST_NAME",
                    "value": ""
                },
                {
                    "key": "EMAIL",
                    "value": ""
                }
            ]
        },
        {
            "key": "USERDATA",
            "children": [
                {
                    "key": "PET_NAME",
                    "value": null
                },
                {
                    "key": "BIRTHDAY",
                    "value": null
                }
            ]
        }
    ]
}
>
```

# GDPR Flow

### Flow when the whole stack is in use

```mermaid
sequenceDiagram
    actor User
    participant Profile UI
    participant Profile Backend
    participant Service GDPR API
    participant Tunnistamo
    User->>+Profile UI: Download my data
    Profile UI->>+Profile Backend: Get data
    Profile Backend->>+Tunnistamo: Get API token
    Tunnistamo-->>-Profile Backend: API token
    Profile Backend->>+Service GDPR API: Get data
    Service GDPR API->>+Tunnistamo: Get public key
    Tunnistamo-->>-Service GDPR API: Public key
    Service GDPR API->>Service GDPR API: Validate API token
    Service GDPR API-->>-Profile Backend: Return data
    Profile Backend-->>-Profile UI: Return data
    Profile UI-->>-User: Return data
```

### Flow when using the GDPR API Tester

```mermaid
sequenceDiagram
    actor Tester
    participant GDPR API Tester
    participant Service GDPR API
    GDPR API Tester->>GDPR API Tester: Generate RSA key
    Tester->>+GDPR API Tester: query
    GDPR API Tester->>GDPR API Tester: Generate API token
    GDPR API Tester->>+Service GDPR API: Get data
    Service GDPR API->>+GDPR API Tester: Get public key
    GDPR API Tester-->>-Service GDPR API: public key
    Service GDPR API->>Service GDPR API: Validate API token
    Service GDPR API-->>-GDPR API Tester: Return data
    GDPR API Tester-->>-Tester: Display data
```
