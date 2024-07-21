import os

# Constants
BASE_DIR = os.path.expanduser('~/.mojodex')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials')
TMP_WAV_FILE = os.path.join(BASE_DIR, 'recording_buffer.wav')
SERVER_URL = 'http://localhost:5001'

CURRENT_STATE = ""

CURRENT_STEP = None
