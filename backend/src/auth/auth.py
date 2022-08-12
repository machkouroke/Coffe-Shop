import json
from flask import request, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from dotenv import load_dotenv
import os

load_dotenv()
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
ALGORITHMS = os.environ.get("ALGORITHMS")
API_AUDIENCE = os.environ.get("API_AUDIENCE")


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    # check if authorization is not in request
    if 'Authorization' not in request.headers:
        abort(401, "Authorization header is expected")
    # get the token
    auth_header = request.headers['Authorization']
    header_parts = auth_header.split(' ')
    # check if token is valid
    if len(header_parts) != 2 or header_parts[0].lower() != 'bearer':
        abort(401, "Authorization header must be Bearer token")
    return header_parts[1]


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True


def verify_decode_jwt(token):
    print(request.headers["Authorization"])
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            return jwt.decode(token, rsa_key, algorithms=ALGORITHMS, audience=API_AUDIENCE,
                              issuer=f'https://{AUTH0_DOMAIN}/')


        except jwt.ExpiredSignatureError as e:
            raise AuthError({'code': 'token_expired', 'description': 'Token expired.'}, 401) from e

        except jwt.JWTClaimsError as e:
            raise AuthError(
                {'code': 'invalid_claims', 'description': 'Incorrect claims. Please, check the audience and issuer.'},
                401) from e

        except Exception as e:
            raise AuthError({'code': 'invalid_header', 'description': 'Unable to parse authentication token.'},
                            400) from e

    raise AuthError({
        'code': 'invalid_header',
        'description': f'Unable to find the appropriate key., {request.headers["Authorization"]}'
    }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(*args, **kwargs)

        return wrapper

    return requires_auth_decorator
