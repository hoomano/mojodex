# Mojodex Scheduler

The scheduler is responsible for running tasks at specific times or intervals.
It is useful for running tasks that are not directly related to a user's request, like sending emails or notifs to a group of users.
It is also useful for proactivity, to let Mojo work on something by checking state of a user or a task at a certain frequency and act accordingly.

## Functionalities
Mojodex's Scheduler has 2 main directory containing:

- Scheduled tasks `scheduler/app/scheduled_tasks`
- Time based tasks `scheduler/app/time_based_tasks`

Those tasks are run thanks to the `scheduler/app/main.py` file that keeps the scheduler running and checks for tasks to run using the `schedule` library.

```python
while True:
    schedule.run_pending()
    time.sleep(1)
```

### Scheduled tasks
Scheduled tasks contains code that are run at a specific frequency. 
```python
### Abstract class named ScheduledTask that has a method job() and a constructor that runs  schedule.every(X).seconds.do(job), X being the number of seconds between executions (param)
from abc import ABC, abstractmethod
import schedule

class ScheduledTask(ABC):

    def __init__(self, n_seconds):
        schedule.every(n_seconds).seconds.do(self.job)

    @abstractmethod
    def job(self):
        """Method that will be executed every n_seconds seconds"""
        pass
```

As Mojodex's Scheduler does not have database access, Scheduled tasks jobs are Backend API calls. Performed at a regular interval, they are useful for checking the state of a user or a task and act accordingly.

The Scheduled tasks are implemented in the `scheduler/app/main.py` file.

```python
[...]
# Scheduled tasks
PurchasesExpirationChecker(3600) # check ended free_plan every 1 hour
ExtractTodos(600) # extract todos every 10 minutes
RescheduleTodos(3600) # reschedule todos every 1 hour
if push_notifications:
    SendDailyNotifications(3600) # send daily notifications every 1 hour (filtered by timezone)
if emails:
    #SendDailyEmails(3600) # send daily emails every 1 hour (filtered by timezone)
    SendTodoDailyEmails(3600) # send todo daily emails every 1 hour (filtered by timezone)
    CheckDisengagedFreeTrialUsers(86400)  # check disengaged free trial users every day
FirstHomeChatOfWeek(3600)
[...]
```

### Time based tasks
Time based tasks contains code that are run at a specific time of the day. 
```python
from abc import ABC, abstractmethod
import schedule


class TimeBasedTask(ABC):

    def __init__(self, hour=10, minute=0, second=0, weekday=None,):
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
```

For now, Mojodex Scheduler doesn't have any time based tasks. Indeed, when running code for a user at a specific time, it is often more relevant to adapt to the user's timezone (for example, to process To-Do rescheduling while user is sleeping). 
Therefore, a Scheduled task is more appropriate to trigger a backend call every hour and filter the concerned users by timezone.

## System 1/System 2 Abstraction

In alignment with the System 1/System 2 framework, **Mojodex's Scheduler embodies a proactive aspect akin to System 2 thinking.**

It functions as the deliberate planner within Mojodex, orchestrating scheduled code execution and empowering the assistant to take preemptive actions based on predefined criteria. Just as System 2 engages in deliberate planning and decision-making, the Scheduler ensures the efficient and effective operation of Mojodex by executing tasks at specific times or intervals, optimizing the assistant's performance in a systematic and thoughtful manner.
