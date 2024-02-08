import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class RescheduleTodos(ScheduledTask):
    logger_prefix = "RescheduleTodos"

    def job(self):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/todos_scheduling"
            pload = {'datetime': datetime.now().isoformat() }
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error rescheduling todos : {internal_request.text}")
            else:
                self.logger.info(f"Todos successfully rescheduled.")
        except Exception as e:
            self.logger.error(f"Error extracting todos : {e}")