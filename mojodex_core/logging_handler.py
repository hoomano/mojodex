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

try:
    from mojodex_core.email_sender import MojoAwsMail
    mojo_mail_client = MojoAwsMail(sender_name=os.environ['SENDER_NAME'], sender_email=os.environ['SENDER_EMAIL'],
                                   region="eu-west-3")
except Exception as e:
    core_logger.error(f"Can't initialize MojoAwsMail : {e}")
    mojo_mail_client = None



def send_admin_email(subject, recipients, text):
    try:
        if mojo_mail_client:
            mojo_mail_client.send_mail(subject=subject,
                                       recipients=recipients,
                                       text=text)
    except Exception as e:
        core_logger.error(f"Error while sending admin email : {e}")


admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []


def send_admin_error_email(error_message):
    try:
        mojo_mail_client.send_mail(subject=f"MOJODEX BACKGROUND ERROR - {os.environ['ENVIRONMENT']}",
                                       recipients=technical_email_receivers,
                                       text=error_message)
    except Exception as e:
        core_logger.error(f"Error while sending admin email : {e}")


def log_error(error_message, session_id=None, notify_admin=False):
    try:
        core_logger.error(error_message)
        error = MdError(session_id=session_id, message=str(error_message),
                        creation_date=datetime.now())
        db_session.add(error)
        db_session.commit()
        if notify_admin:
            send_admin_email(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                             recipients=technical_email_receivers,
                             text=str(error_message))
    except Exception as e:
        db_session.rollback()
        core_logger.error(f"Error while storing error to database: {e}")

