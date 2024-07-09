import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class RescheduleTodos(ScheduledTask):
    logger_prefix = "RescheduleTodos"

    def job(self):
        try:
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/reschedule_todo"
            pload = {'datetime': datetime.now().isoformat() }
            headers = {'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error rescheduling todos : {internal_request.text}")
            else:
                self.logger.info(f"Todos successfully rescheduled.")
        except Exception as e:
            self.logger.error(f"Error extracting todos : {e}")