import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class UpdateUserPreferences(ScheduledTask):
    logger_prefix = "UpdateUserPreferences"

    def job(self):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/update_user_preferences"
            pload = {'datetime': datetime.now().isoformat() }
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error updating user preferences : {internal_request.text}")
            else:
                self.logger.info(f"User preferences update lauched")
        except Exception as e:
            self.logger.error(f"Error updating user preferences : {e}")