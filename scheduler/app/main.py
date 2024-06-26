import os

import requests
import schedule
import time
from scheduled_tasks.check_disengaged_free_users import CheckDisengagedFreeTrialUsers
from scheduled_tasks.send_daily_emails import SendDailyEmails
from scheduled_tasks.send_daily_notifications import SendDailyNotifications
from scheduled_tasks.extract_todos import ExtractTodos
from scheduled_tasks.reschedule_todos import RescheduleTodos
from scheduled_tasks.send_todo_daily_emails import SendTodoDailyEmails
from scheduled_tasks.purchase_expiration_checker import PurchasesExpirationChecker
from scheduled_tasks.send_calendar_suggestion_notifications import CalendarSuggestionNotificationSender
from scheduled_tasks.first_home_chat_of_week import FirstHomeChatOfWeek
from scheduled_tasks.relaunch_locked_steps import RelaunchLockedSteps
from datetime import datetime

from scheduler_logger import SchedulerLogger

logger = SchedulerLogger("main", file_path=f"./main.log")

def _check_emails_are_configured():
    # http request to backend
    try:
        uri = f"{os.environ['MOJODEX_BACKEND_URI']}/is_email_service_configured"
        args = {'datetime': datetime.now().isoformat()}
        internal_request = requests.get(uri, params=args)
        if internal_request.status_code != 200:
            logger.error(f"Error checking email service configuration : {internal_request.content}")
            return False
        else:
            is_configured = internal_request.json()["is_configured"]
            if not is_configured:
                logger.warning(f"Email service is not configured")
            else:
                logger.info(f"Email service is configured")
            return is_configured
    except Exception as e:
        logger.error(f"Error checking email service configuration : {e}")
        return False

def _check_push_notifications_are_configured():
    # http request to backend
    try:
        uri = f"{os.environ['MOJODEX_BACKEND_URI']}/is_push_notif_service_configured"
        args = {'datetime': datetime.now().isoformat()}
        headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET']}
        internal_request = requests.get(uri, params=args, headers=headers)
        if internal_request.status_code != 200:
            logger.error(f"Error checking push notification service configuration : {internal_request.content}")
            return False
        else:
            is_configured = internal_request.json()["is_configured"]
            if not is_configured:
                logger.warning(f"Push notification service is not configured")
            else:
                logger.info(f"Push notification service is configured")
            return is_configured
    except Exception as e:
        logger.error(f"Error checking push notification service configuration : {e}")
        return False


# Scheduled tasks
PurchasesExpirationChecker(3600) # check ended free_plan every 1 hour
ExtractTodos(600) # extract todos every 10 minutes
RescheduleTodos(3600) # reschedule todos every 1 hour
if _check_push_notifications_are_configured():
    CalendarSuggestionNotificationSender(600) # send calendar suggestion notifications every 10 minutes
    SendDailyNotifications(3600) # send daily notifications every 1 hour (filtered by timezone)
if _check_emails_are_configured():
    #SendDailyEmails(3600) # send daily emails every 1 hour (filtered by timezone)
    SendTodoDailyEmails(3600) # send todo daily emails every 1 hour (filtered by timezone)
    CheckDisengagedFreeTrialUsers(86400)  # check disengaged free trial users every day
FirstHomeChatOfWeek(3600)
RelaunchLockedSteps(7200) # relaunch locked steps every 2 hours

# Time based tasks


while True:
    schedule.run_pending()
    time.sleep(1)
