from functools import wraps
import os
from flask_restful import request
import jwt


def authenticate_function(token):
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=os.environ["ENCODING_ALGORITHM"])
        user_id = payload["sub"].split(os.environ['TOKEN_SECRET_SPLITTER'])[0]
        return True, user_id
    except KeyError:
        return {"error": "Authorization key required"}, 403
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired."}, 403
    except jwt.InvalidTokenError:
        return {"error": "Invalid token."}, 403


def authenticate(methods=["PUT", "POST", "DELETE", "GET"]):
    methods = [name.lower() for name in methods]

    def authenticate_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if func.__name__ not in methods:
                return func(*args, **kwargs)
            try:
                token = request.headers['Authorization']
                auth = authenticate_function(token)
                if auth[0] is not True:
                    return auth
                else:
                    kwargs["user_id"] = auth[1]
            except Exception as e:
                return {"error": f"Authentication error : {e}"}, 403

            return func(*args, **kwargs)

        return wrapper

    return authenticate_wrapper

def _authenticate_with_secret(secret, methods=["PUT", "POST", "DELETE", "GET"]):
    methods = [name.lower() for name in methods]

    def authenticate_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if func.__name__ not in methods:
                return func(*args, **kwargs)
            try:
                if request.headers['Authorization'] != secret:
                    raise Exception("Invalid secret")
            except Exception as e:
                return {"error": f"Authentication error : {e}"}, 403

            return func(*args, **kwargs)

        return wrapper

    return authenticate_wrapper

def authenticate_with_backoffice_secret(methods=["PUT", "POST", "DELETE", "GET"]):
    return _authenticate_with_secret(os.environ["BACKOFFICE_SECRET"], methods)

def authenticate_with_scheduler_secret(methods=["PUT", "POST", "DELETE", "GET"]):
    return _authenticate_with_secret(os.environ["MOJODEX_SCHEDULER_SECRET"], methods)
