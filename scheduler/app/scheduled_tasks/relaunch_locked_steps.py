import os
from datetime import datetime
from scheduled_tasks.scheduled_task import ScheduledTask
import requests

class RelaunchLockedSteps(ScheduledTask):
    logger_prefix = "RelaunchLockedSteps"

    def job(self):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/relaunch_locked_workflow_step_executions"
            pload = {'datetime': datetime.now().isoformat() }
            headers = {'Authorization': os.environ['MOJODEX_SCHEDULER_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(f"Error relaunching locked steps : {internal_request.text}")
            else:
                user_workflow_step_executions_pk = internal_request.json()['user_workflow_step_executions_pk']
                self.logger.info(f"Relaunch successful. {len(user_workflow_step_executions_pk)} locked steps are concerned.")
        except Exception as e:
            self.logger.error(f"Error relaunching locked steps : {e}")