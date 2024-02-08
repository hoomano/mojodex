from datetime import datetime
from costs_manager.costs_manager import CostsManager
from app import send_admin_error_email

class SerpAPICostsManager(CostsManager):
    logger_prefix = "SerpAPICostsManager"
    name = "serp_api"
    columns = ["datetime","user_id", "num_of_results_asked", "user_task_execution_pk", "task_name_for_system"]

    def __init__(self):
        try:
            super().__init__(SerpAPICostsManager.name, SerpAPICostsManager.columns)
        except Exception as e:
            send_admin_error_email(f"{SerpAPICostsManager.logger_prefix}: __init__: {e}")


    def on_search(self, user_id, num_of_results_asked, user_task_execution_pk, task_name_for_system):
        try:
            with open(self.file_path, "a") as f:
                f.write(f"{datetime.utcnow().isoformat()},{user_id},{num_of_results_asked},{user_task_execution_pk},{task_name_for_system}\n")
        except Exception as e:
            send_admin_error_email(f"{SerpAPICostsManager.logger_prefix}: on_search: {e}")