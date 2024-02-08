import os
from datetime import datetime
import requests
from scheduled_tasks.scheduled_task import ScheduledTask


class CheckDisengagedFreeTrialUsers(ScheduledTask):
    logger_prefix = "CheckDisengagedFreeTrialUsers"

    def job(self, offset=0, batch_size=50):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/check_disengaged_free_trial_users"
            pload = {'datetime': datetime.now().isoformat(), 'n_disengaged_users': batch_size, 'offset': offset}
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error checking for disengaged free trial users : {internal_request.text}")
            else:
                user_ids = internal_request.json()['user_ids']
                self.logger.info(f"Check successful. {len(user_ids)} users are concerned.")
                if len(user_ids) == batch_size:
                    self.job(offset=offset+batch_size)
        except Exception as e:
            self.logger.error(f"Error sending disengaged free trial users : {e}")