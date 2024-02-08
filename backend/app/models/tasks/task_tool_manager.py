from app import db
from db_models import MdTaskToolExecution
from mojodex_backend_logger import MojodexBackendLogger


class TaskToolManager:
    logger_prefix = "TaskToolManager::"
    tool_name_start_tag, tool_name_end_tag = "<tool_to_use>", "</tool_to_use>"
    tool_usage_start_tag, tool_usage_end_tag = "<tool_usage>", "</tool_usage>"

    def __init__(self, session_id, remove_tags_function):
        self.logger = MojodexBackendLogger(f"{TaskToolManager.logger_prefix} -- session_id {session_id}")
        self.remove_tags_function = remove_tags_function

    def _find_task_tool_association(self, tool_name, task_tool_associations):
        # first task_tool_associations where task_tool_association.tool.name == tool_name, if not, answer null
        # If null, it will crash => maybe try again ? todo
        self.logger.info(f"_find_task_tool_association : tool_name {tool_name} \n task_tool_associations: {task_tool_associations}")
        return next((task_tool_association for task_tool_association in task_tool_associations if task_tool_association['tool_name'] == tool_name), None)



    def manage_tool_usage_text(self, text, user_task_execution_pk, task_tool_associations_json):
        try:
            mojo_text = self.remove_tags_function(text, self.tool_usage_start_tag, self.tool_usage_end_tag)
            tool_name = self.remove_tags_function(text, self.tool_name_start_tag, self.tool_name_end_tag)
            task_tool_execution = MdTaskToolExecution(
                task_tool_association_fk=self._find_task_tool_association(tool_name, task_tool_associations_json)['task_tool_association_pk'],
                user_task_execution_fk=user_task_execution_pk)
            db.session.add(task_tool_execution)
            db.session.commit()
            db.session.refresh(task_tool_execution)
            return {"text": mojo_text,
                    "text_with_tags": text,
                    "task_tool_execution_fk": task_tool_execution.task_tool_execution_pk}
        except Exception as e:
            raise Exception(f"{TaskToolManager.logger_prefix} :: manage_tool_usage_text :: {e}")
