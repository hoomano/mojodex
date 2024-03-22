import logging
import os
from datetime import datetime

from mojodex_core.entities import MdError
from mojodex_core.db import db_session

class EmojiFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):
        emoji = ''
        if record.levelno == logging.DEBUG:
            emoji = '🟣'
        if record.levelno == logging.INFO:
            emoji = '🟢'
        elif record.levelno == logging.WARNING:
            emoji = '🟠'
        elif record.levelno == logging.ERROR:
            emoji = '🔴'
        record.msg = f'{emoji} {record.name} :: {record.msg}'
        return super().format(record)

class MojodexCoreLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name, level=logging.NOTSET)
        formatter = EmojiFormatter()
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.addHandler(stream_handler)
        # switch on if os.environ.get("LOG_LEVEL") to set level
        log_level = os.environ.get("LOG_LEVEL")
        if log_level == "debug":
            self.setLevel(logging.DEBUG)
        elif log_level == "info":
            self.setLevel(logging.INFO)
        elif log_level == "warning":
            self.setLevel(logging.WARNING)
        elif log_level == "error":
            self.setLevel(logging.ERROR)
        else: # default
            self.setLevel(logging.DEBUG)


core_logger = MojodexCoreLogger("core_logger")

def log_error(error_message, session_id=None, notify_admin=False):
    try:
        core_logger.error(error_message)
        error = MdError(session_id=session_id, message=str(error_message),
                        creation_date=datetime.now())
        db_session.add(error)
        db_session.commit()
        if notify_admin:
            from mojodex_core.mail import send_admin_email, technical_email_receivers
            send_admin_email(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                             recipients=technical_email_receivers,
                             text=str(error_message))
    except Exception as e:
        db_session.rollback()
        core_logger.error(f"Error while storing error to database: {e}")


def on_json_error(result, function_name, retries):
    error_path = f"/data/{function_name}_{datetime.now().isoformat()}.txt"
    with open(error_path, "w") as f:
        f.write(result)
    raise Exception(
        f"{function_name} - incorrect JSON: aborting after {retries} retries...  data available in {error_path}")

