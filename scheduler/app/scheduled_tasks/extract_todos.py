import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class ExtractTodos(ScheduledTask):
    logger_prefix = "ExtractTodos"

    def job(self):
        try:
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/extract_todos"
            pload = {'datetime': datetime.now().isoformat() }
            headers = {'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error extracting todos : {internal_request.text}")
            else:
                self.logger.info(f"Todos successfully extracted.")
        except Exception as e:
            self.logger.error(f"Error extracting todos : {e}")