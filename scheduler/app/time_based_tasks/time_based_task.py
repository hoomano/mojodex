### Abstract class named ScheduledTask that has a method job() and a constructor that runs  schedule.every(X).seconds.do(job), X being the number of seconds between executions (param)
from abc import ABC, abstractmethod
import schedule
from scheduler_logger import SchedulerLogger


class TimeBasedTask(ABC):
    logger_prefix = "TimeBasedTask"

    def __init__(self, hour=10, minute=0, second=0, weekday=None,):
        self.logger = SchedulerLogger(self.logger_prefix, file_path=f"./{self.logger_prefix}.log")
        if weekday is not None:
            schedule.every().monday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 0 else None
            schedule.every().tuesday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 1 else None
            schedule.every().wednesday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 2 else None
            schedule.every().thursday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 3 else None
            schedule.every().friday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 4 else None
            schedule.every().saturday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 5 else None
            schedule.every().sunday.at(f"{hour}:{minute}:{second}").do(self.job) if weekday == 6 else None
        else:
            schedule.every().day.at(f"{hour}:{minute}:{second}").do(self.job)


    @abstractmethod
    def job(self):
        """Method that will be executed at the specified time"""
        pass