### Abstract class named ScheduledTask that has a method job() and a constructor that runs  schedule.every(X).seconds.do(job), X being the number of seconds between executions (param)
from abc import ABC, abstractmethod
import schedule
from scheduler_logger import SchedulerLogger


class ScheduledTask(ABC):
    logger_prefix = "ScheduledTask"

    def __init__(self, n_seconds):
        self.logger = SchedulerLogger(self.logger_prefix, file_path=f"./{self.logger_prefix}.log")
        self.logger.info(f"Starting {self.logger_prefix} with a frequency of {n_seconds} seconds")
        schedule.every(n_seconds).seconds.do(self.job)

    @abstractmethod
    def job(self):
        """Method that will be executed every n_seconds seconds"""
        pass