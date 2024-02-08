import logging
from pythonjsonlogger import jsonlogger

class TimingLogger:

    def __init__(self, log_file):
        log_handler = logging.FileHandler(log_file, mode='a', encoding=None, delay=True)
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(message)s %(duration)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        log_handler.setFormatter(formatter)
        self.logger = logging.Logger('timing_logger')
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)

    def log_timing(self, start_time, end_time, event_name):
        duration = end_time - start_time
        self.logger.info('%s', event_name, extra={'duration': duration})
        for handler in self.logger.handlers:
            handler.flush()



