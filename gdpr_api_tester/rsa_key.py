import rsa
from jose import jwk
from jose.backends.base import Key
from jose.constants import ALGORITHMS


def _get_or_create_rsa_key() -> Key:
    """Gets or creates an RSA key

    The generated RSA key is saved in PEM format to the current directory in a file
    named "gdpr_api_tester_key.pem".
    """
    key = None
    print(
        "Trying to load RSA key from file gdpr_api_tester_key.pem...",
        end="",
        flush=True,
    )
    try:
        with open("gdpr_api_tester_key.pem", "r") as f:
            pem_data = f.read()
        key = jwk.construct(pem_data, ALGORITHMS.RS256)
        print("ok.", flush=True)
    except FileNotFoundError:
        print("not found.", flush=True)
    except PermissionError:
        print("could not read.", flush=True)

    if not key:
        print(
            "Generating new RSA key and saving it to gdpr_api_tester_key.pem...",
            end="",
            flush=True,
        )
        # Pubkey isn't saved as the public key can be derived from the private key
        # when needed.
        (pubkey, privkey) = rsa.newkeys(2048)
        try:
            with open("gdpr_api_tester_key.pem", "wb") as f:
                f.write(privkey.save_pkcs1())

            print("ok.", flush=True)
        except PermissionError:
            print("could not write.", flush=True)

        key = jwk.construct(privkey, ALGORITHMS.RS256)

    return key


# kid and rsa_keys are effectively singletons as Python doesn't run the code multiple
# times when importing.
# Key id is set here so that the JWT encoding and jwks view can easily use the same name
kid = "gdpr-api-tester-key"
rsa_key = _get_or_create_rsa_key()
