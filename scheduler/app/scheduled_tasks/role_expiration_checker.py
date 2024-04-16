import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class RolesExpirationChecker(ScheduledTask):
    logger_prefix = "RolesExpirationChecker"

    def job(self, batch_size=50):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/check_expired_roles"
            pload = {'datetime': datetime.now().isoformat(),
                     "n_roles": batch_size}
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error checking for expired roles : {internal_request.text}")
            else:
                role_pks = internal_request.json()['role_pks']
                if len(role_pks) == batch_size:
                    self.job()
                else:
                    self.logger.info(f"Expired roles check successful.")
        except Exception as e:
            self.logger.error(f"Error checking for expired roles : {e}")