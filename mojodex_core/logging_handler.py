import logging
import os
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdError
from datetime import datetime
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

@with_db_session
def log_error(error_message, db_session, session_id=None, notify_admin=False):
    try:
        core_logger.error(error_message)
        error = MdError(session_id=session_id, message=str(error_message),
                        creation_date=datetime.now())
        if db_session is None:
            db_session.add(error)
            db_session.commit()
        if notify_admin:
            from mojodex_core.email_sender.email_service import EmailService
            EmailService().send_technical_error_email(error_message=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}\n{error_message}")
    except Exception as e:
        if db_session is not None:
            db_session.rollback()
        core_logger.error(f"Error while storing error to database: {e}")


def on_json_error(result, function_name, retries):
    error_path = f"/data/{function_name}_{datetime.now().isoformat()}.txt"
    with open(error_path, "w") as f:
        f.write(result)
    raise Exception(
        f"{function_name} - incorrect JSON: aborting after {retries} retries...  data available in {error_path}")

