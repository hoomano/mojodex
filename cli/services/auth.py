from functools import wraps
import requests
from entities.user import User
from constants import *
import os
from getpass import getpass


def _load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            # Return email, username, token
            return file.read().strip().split(':')
    except FileNotFoundError:
        return None, None, None


def _login():
    email = input('Email: ')
    password = getpass('Password: ')
    response = requests.post(f'{SERVER_URL}/user', json={'email': email,
                                'password': password, "login_method": "email_password", "datetime": "now"})
    if response.status_code == 200:
        data = response.json()
        save_credentials(email, data['name'], data['token'])
        return email, data['name'], data['token']
    else:
        raise Exception("Incorrect credentials")


def login() -> User:
    try:
        email, username, token = _load_credentials()
        if not token:
            email, username, token = _login()
        
        return User(email, username, token)
        
    except Exception as e:
        raise Exception(f"Failed to login: {e}")
        
    
def save_credentials(email, username, token):
    try:
        _ensure_dir()
        with open(CREDENTIALS_FILE, 'w') as file:
            file.write(f"{email}:{username}:{token}")
    except Exception as e:
        raise Exception(f"Failed to save credentials: {e}")


def _ensure_dir():
    try:
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)
    except Exception as e:
        raise Exception(f"Failed to create directory: {e}")


# Wrapper to ensure that the user is authenticated
def ensure_authenticated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            user = login()
            return func(*args, token=user.token, **kwargs)
        except Exception as e:
            raise Exception(f"ensure_authenticated :: {e}")
    return wrapper