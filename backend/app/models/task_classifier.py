import time

from app import db, log_error, timing_logger
import os
from mojodex_core.entities import *
from jinja2 import Template

from mojodex_backend_logger import MojodexBackendLogger

from app import llm, llm_conf, llm_backup_conf


class TaskClassifier:
    logger_prefix = "TaskClassifier::"
    task_classification_prompt = "/data/prompts/task_classification_prompt.txt"

    task_classifier = llm(llm_conf, label="TASK_CLASSIFICATION",
                                    llm_backup_conf=llm_backup_conf)

    def __init__(self, user_id):
        try:
            self.logger = MojodexBackendLogger(f"{TaskClassifier.logger_prefix}")
            self.user_id = user_id
            self.tasks = db.session.query(MdTask) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .filter(MdUserTask.user_id == user_id) \
                .filter(MdUserTask.enabled == True) \
                .all()
            with open(TaskClassifier.task_classification_prompt, "r") as f:
                self.prompt_template = Template(f.read())
        except Exception as e:
            raise Exception(f"{TaskClassifier.logger_prefix} :: __init__ :: {e}")

    def classify(self, conversation):
        try:
            self.logger.info(f"{TaskClassifier.logger_prefix} :: classify")
            start_time = time.time()
            classification_prompt = self.prompt_template.render(conversation=conversation, tasks=self.tasks)
            messages = [{"role": "user", "content": classification_prompt}]

            responses = TaskClassifier.task_classifier.chat(messages, self.user_id,
                                                            temperature=0, max_tokens=10)
            task_name = responses[0].strip().lower()
            self.logger.info(f"{TaskClassifier.logger_prefix} :: classify :: task_name={task_name}")
            # is task_name in self.tasks?
            task = next((task for task in self.tasks if task.name_for_system == task_name), None)
            end_time = time.time()
            timing_logger.log_timing(start_time, end_time, f"{TaskClassifier.logger_prefix} :: classify")
            return task
        except Exception as e:
            raise Exception(f"{TaskClassifier.logger_prefix} :: classify :: {e}")
