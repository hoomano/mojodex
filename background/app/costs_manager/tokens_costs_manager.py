from datetime import datetime
from costs_manager.costs_manager import CostsManager
from app import send_admin_error_email


class TokensCostsManager(CostsManager):
    logger_prefix = "TokensCostsManager"
    name = "tokens"
    columns = ["datetime","user_id", "n_prompts_tokens", "n_conversation_tokens", "n_response_tokens", "engine", "name",
               "user_task_execution_pk", "task_name_for_system"]

    def __init__(self):
        try:
            super().__init__(TokensCostsManager.name, TokensCostsManager.columns)
        except Exception as e:
            send_admin_error_email(f"{TokensCostsManager.logger_prefix}: __init__: {e}")


    def on_tokens_counted(self, user_id, n_prompts_tokens, n_conversation_tokens, n_response_tokens, model, name,
                           user_task_execution_pk, task_name_for_system):
        try:
            with open(self.file_path, "a") as f:
                f.write(f"{datetime.utcnow().isoformat()},{user_id},{n_prompts_tokens},{n_conversation_tokens},{n_response_tokens},{model},{name},"
                        f"{user_task_execution_pk},{task_name_for_system}\n")
        except Exception as e:
            send_admin_error_email(f"{TokensCostsManager.logger_prefix}: on_tokens_counted: {e}")