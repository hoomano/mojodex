import base64
import os
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import json
import requests


class AppleLoginManager:
    apple_token_uri = "https://appleid.apple.com/auth/token"

    def __init__(self):
        try:
            self.apple_service_client_id = os.environ['APPLE_CLIENT_ID']
            self.apple_app_client_id = os.environ['APPLE_ID']
            self.client_app_secret = os.environ['APPLE_CLIENT_APP_SECRET']
        except Exception as e:
            raise Exception(f"AppleLoginManager - __init__ : {e}")


    def login(self, authorization_code, token):
        try:
            if authorization_code:
                return self._login_from_authorization_code(authorization_code)
            elif token:
                return self._login_from_token(token, audience=self.apple_service_client_id)
            else:
                raise Exception("No authorization_code or token provided")
        except Exception as e:
            raise Exception(f"AppleLoginManager - login : {e}")
            
     # Convert Base64URL to Base64
    
    def _base64url_to_base64(self, base64url):
        base64 = base64url.replace('-', '+').replace('_', '/')
        padding = len(base64) % 4
        if padding:
            base64 += '=' * (4 - padding)
        return base64
    
    def _get_kid(self, token):
        try:
            # Split the JWT token into header, payload, and signature
            header_base64 = token.split('.')[0]

            # Decode the header from base64
            decoded_header = base64.urlsafe_b64decode(header_base64 + "===").decode("utf-8")
            # Parse the JSON content of the header
            header_data = json.loads(decoded_header)
            kid = header_data['kid']
            return kid
        except Exception as e:
            raise Exception(f"_get_kid: {e}")

    def _get_public_key(self, kid):
        try:
            # Fetch https://appleid.apple.com/auth/keys to get the public key
            # and find the public key with the matching kid
            r = requests.get('https://appleid.apple.com/auth/keys')

            public_key = next(key for key in r.json()['keys'] if key['kid'] == kid)
            n_base64url, e_base64url = public_key['n'], public_key['e']

            n_base64 = self._base64url_to_base64(n_base64url)
            e_base64 = self._base64url_to_base64(e_base64url)
            # Convert Base64 to Decimal
            n_decimal = int.from_bytes(base64.b64decode(n_base64), byteorder='big')
            e_decimal = int.from_bytes(base64.b64decode(e_base64), byteorder='big')

            public_key = rsa.RSAPublicNumbers(e_decimal, n_decimal).public_key()
            return public_key
        except Exception as e:
            raise Exception(f"_get_public_key: {e}")

    def _login_from_token(self, token, audience):
        try:
            kid = self._get_kid(token)
            public_key = self._get_public_key(kid)

            decoded = jwt.decode(token, public_key, algorithms=['RS256'], audience=audience)

            apple_id = decoded["sub"]

            # name = what is before @ of email because apple does not provide name in token
            email = decoded["email"]
            name = email.split("@")[0]
            return apple_id, name, email
        except jwt.exceptions.InvalidTokenError as e:
            raise Exception(f"_login_from_token - InvalidTokenError : {e}")
        except Exception as e:
            raise Exception(f"_login_from_token: {e}")
        
    def _generate_token_from_authorization_code(self, authorization_code):
        try:
            headers = {"content-type": "application/x-www-form-urlencoded"}

            data = {
                "client_id": self.apple_app_client_id,
                "client_secret": self.client_app_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
            }
            res = requests.post(self.apple_token_uri, data=data, headers=headers)
            values = res.json()
            id_token = values["id_token"]
            return id_token
        except Exception as e:
            raise Exception(f"_generate_token_from_authorization_code: {e}")

    def _login_from_authorization_code(self, authorization_code):
        try:
            token = self._generate_token_from_authorization_code(authorization_code)
            return self._login_from_token(token, audience=self.apple_app_client_id)
        except Exception as e:
            raise Exception(f"_login_from_authorization_code: {e}")