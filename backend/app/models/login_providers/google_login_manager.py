import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

class GoogleLoginManager:
    def __init__(self):
        try:
            self.google_client_id = os.environ['GOOGLE_CLIENT_ID']
        except Exception as e:
            raise Exception(f"GoogleLoginManager - __init__ : {e}")
        
    def login(self, token):
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), self.google_client_id)
            google_id = idinfo['sub']
            name = idinfo['name']
            email = idinfo['email']
            return google_id, name, email
        except Exception as e:
            raise Exception(f"GoogleLoginManager - login : {e}")