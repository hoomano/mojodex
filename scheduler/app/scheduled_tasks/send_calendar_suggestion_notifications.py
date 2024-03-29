import os
from datetime import datetime, timedelta, timezone
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class CalendarSuggestionNotificationSender(ScheduledTask):
    logger_prefix = "CalendarSuggestionNotificationSender"

    def job(self, offset=0, since_date=None, until_date=None, batch_size=50):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/calendar_suggestion_notifications"
            now_date = datetime.now(timezone.utc)
            since_date = since_date if since_date else now_date - timedelta(seconds=600)
            until_date = now_date if until_date is None else until_date
            pload = {'datetime': datetime.now().isoformat(),
                     'n_notifications': batch_size, 'offset': offset, 'since_date': since_date.isoformat(), "until_date": until_date.isoformat()}
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error sending calendar suggestion notifications : {internal_request.text}")
            else:
                calendar_suggestion_pks = internal_request.json()['calendar_suggestion_pks']
                self.logger.info(f"Calendar suggestion notifications successfully launched. Those are concerned: {calendar_suggestion_pks}")
                if len(calendar_suggestion_pks) == batch_size:
                    self.job(offset=offset+batch_size, since_date=since_date, until_date=until_date)
        except Exception as e:
            self.logger.error(f"Error sending calendar suggestions notifications : {e}")