
from mojodex_core.costs_manager.costs_manager import CostsManager
from mojodex_core.mail import send_technical_error_email
from datetime import datetime, timezone

class NewsAPICostsManager(CostsManager):
    logger_prefix = "NewsAPICostsManager"
    name = "news_api"
    columns = ["datetime","user_id", "num_of_results_asked", "user_task_execution_pk", "task_name_for_system"]

    def __init__(self):
        try:
            super().__init__(NewsAPICostsManager.name, NewsAPICostsManager.columns)
        except Exception as e:
            send_technical_error_email(f"{NewsAPICostsManager.logger_prefix}: __init__: {e}")


    def on_search(self, user_id, num_of_results_asked, user_task_execution_pk, task_name_for_system):
        try:
            with open(self.file_path, "a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()},{user_id},{num_of_results_asked},{user_task_execution_pk},{task_name_for_system}\n")
        except Exception as e:
            send_technical_error_email(f"{NewsAPICostsManager.logger_prefix}: on_search: {e}")