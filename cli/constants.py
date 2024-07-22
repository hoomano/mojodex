import os

# Constants
BASE_DIR = os.path.expanduser('~/.mojodex')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials')
TMP_WAV_FILE = os.path.join(BASE_DIR, 'recording_buffer.wav')
SERVER_URL = 'http://localhost:5001'

CURRENT_STATE = ""

CURRENT_STEP = None
APP_VERSION="0.4.13"

# Setting Platform="mobile" for now because "cli" does not exist yet on the server and functionnalities are closer to mobile than webapp
PLATFORM='mobile' 