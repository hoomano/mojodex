
from mojodex_core.costs_manager.costs_manager import CostsManager
from mojodex_core.logging_handler import log_error
from datetime import datetime, timezone
class WhisperCostsManager(CostsManager):
    logger_prefix = "WhisperCostsManager"
    name = "whisper"
    columns = ["datetime","user_id", "n_seconds", "user_task_execution_pk", "task_name_for_system", "mode"]

    def __init__(self):
        try:
            super().__init__(WhisperCostsManager.name, WhisperCostsManager.columns)
        except Exception as e:
            log_error(f"{WhisperCostsManager.logger_prefix}: __init__: {e}", notify_admin=True)


    def on_seconds_counted(self, user_id, n_seconds, user_task_execution_pk, task_name_for_system, mode):
        try:
            with open(self.file_path, "a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()},{user_id},{n_seconds},{user_task_execution_pk},{task_name_for_system},{mode}\n")
        except Exception as e:
            log_error(f"{WhisperCostsManager.logger_prefix}: on_seconds_counted: {e}", notify_admin=True)