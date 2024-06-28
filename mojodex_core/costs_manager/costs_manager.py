import os

from abc import ABC
from datetime import datetime
class CostsManager(ABC):
    logger_prefix = "CostsManager"
    cost_dir = "/data/costs"

    def __init__(self, name, columns):
        try:
            if not os.path.exists(CostsManager.cost_dir):
                os.makedirs(CostsManager.cost_dir)
            month_year = datetime.now().strftime("%m_%Y")
            first_line = ','.join(columns) + "\n"
            self.dir_path = f"{CostsManager.cost_dir}/{name}"
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path)
            self.file_path = self._create_costs_file(month_year, first_line)
        except Exception as e:
            raise Exception(f"{CostsManager.logger_prefix} : __init__: {e}")

    def _create_costs_file(self, month_year, first_line):
        try:
            file_path = f"{self.dir_path}/{month_year}.csv"
            if not os.path.exists(file_path):
                # create file with columns n_prompts_tokens, n_conversation_tokens, n_response_tokens, model, engine, name
                with open(file_path, "w") as f:
                    f.write(first_line)
            return file_path
        except Exception as e:
            raise Exception(f"{CostsManager.logger_prefix} : _create_costs_file: {e}")



