import logging
import os


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

class BackgroundLogger(logging.Logger):
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

