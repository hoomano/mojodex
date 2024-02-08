import os
from datetime import datetime
import requests
from scheduled_tasks.scheduled_task import ScheduledTask


class FirstHomeChatOfWeek(ScheduledTask):
    logger_prefix = "FirstHomeChatOfWeek"

    def job(self, offset=0, batch_size=50):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/home_chat"
            pload = {'datetime': datetime.now().isoformat(), 'n_users': batch_size, 'offset': offset}
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error preparing first home chats of week : {internal_request.text}")
            else:
                user_ids = internal_request.json()['user_ids']
                self.logger.info(f"Preparation of first home chats successfully launched. : {len(user_ids)} users are concerned.")
                if len(user_ids) == batch_size:
                    self.job(offset=offset+batch_size)
        except Exception as e:
            self.logger.error(f"Error preparing first home chats of week : {e}")