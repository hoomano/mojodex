import os

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

push_notifications = 'FIREBASE_PROJECT_ID' in os.environ and os.environ['FIREBASE_PROJECT_ID']
emails = 'AWS_ACCESS_KEY_ID' in os.environ and os.environ['AWS_ACCESS_KEY_ID']

# Scheduled tasks
PurchasesExpirationChecker(3600) # check ended free_plan every 1 hour
ExtractTodos(600) # extract todos every 10 minutes
RescheduleTodos(3600) # reschedule todos every 1 hour
if push_notifications:
    CalendarSuggestionNotificationSender(600) # send calendar suggestion notifications every 10 minutes
    SendDailyNotifications(3600) # send daily notifications every 1 hour (filtered by timezone)
if emails:
    #SendDailyEmails(3600) # send daily emails every 1 hour (filtered by timezone)
    SendTodoDailyEmails(3600) # send todo daily emails every 1 hour (filtered by timezone)
    CheckDisengagedFreeTrialUsers(86400)  # check disengaged free trial users every day
FirstHomeChatOfWeek(3600)
RelaunchLockedSteps(7200) # relaunch locked steps every 2 hours

# Time based tasks


while True:
    schedule.run_pending()
    time.sleep(1)
