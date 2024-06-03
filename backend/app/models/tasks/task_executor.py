from app import db
from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager

from mojodex_core.entities import MdTextType
from mojodex_backend_logger import MojodexBackendLogger


class TaskExecutor:
    logger_prefix = "TaskExecutor::"

    def __init__(self, session_id, user_id):
        self.logger = MojodexBackendLogger(f"{TaskExecutor.logger_prefix} - session_id {session_id}")
        self.session_id=session_id
        self.user_id = user_id

    def manage_execution_text(
        self, execution_text, task, task_name, user_task_execution_pk, use_draft_placeholder=False):
        try:
            self.logger.debug(f"manage_execution_text")

            if InstructTaskProducedTextManager.draft_start_tag in execution_text:
                self.logger.debug(f"InstructTaskProducedTextManager.draft_start_tag in mojo_text")

                produced_text_manager = InstructTaskProducedTextManager(self.session_id, self.user_id, user_task_execution_pk, task.name_for_system, use_draft_placeholder=use_draft_placeholder)
                produced_text, produced_text_version = produced_text_manager.extract_and_save_produced_text_from_tagged_text(
                    execution_text, text_type_pk=task.output_text_type_fk)

                text_type = db.session.query(MdTextType.name).filter(
                    MdTextType.text_type_pk == produced_text_version.text_type_fk).first()[0] if produced_text_version.text_type_fk else None

                message = {
                    "produced_text": produced_text_version.production,
                    "produced_text_title": produced_text_version.title,
                    "produced_text_pk": produced_text.produced_text_pk,
                    "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                    "user_task_execution_pk": user_task_execution_pk,
                    "task_name": task_name,
                    "task_pk": task.task_pk,
                    "task_icon": task.icon,
                    "text_type": text_type,
                    "text": InstructTaskProducedTextManager.remove_tags(execution_text)
                }
                return message

            else:
                self.logger.debug(f"InstructTaskProducedTextManager.draft_start_tag not in mojo_text")
                return {"text": execution_text}
        except Exception as e:
            raise Exception(f"{TaskExecutor.logger_prefix} :: manage_execution_text :: {e}")