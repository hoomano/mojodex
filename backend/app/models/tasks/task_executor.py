import time

from app import db
from mojodex_core.entities import MdTextType
from models.session.assistant_message_generator import AssistantMessageGenerator
from db_models import MdTextType
from models.produced_text_manager import ProducedTextManager
from mojodex_backend_logger import MojodexBackendLogger
from app import socketio_message_sender

from app import timing_logger
from packaging import version

class TaskExecutor:
    logger_prefix = "TaskExecutor::"
    execution_start_tag = "<execution>"
    execution_end_tag = "</execution>"



    def __init__(self, session_id, user_id):
        self.logger = MojodexBackendLogger(f"{TaskExecutor.logger_prefix} - session_id {session_id}")
        self.session_id=session_id
        self.user_id = user_id

    def manage_execution_text(
        self, execution_text, task, task_displayed_data, user_task_execution_pk, use_draft_placeholder=False):
        try:
            self.logger.debug(f"manage_execution_text")
            if self.execution_start_tag and self.execution_end_tag in execution_text:
                mojo_text = AssistantMessageGenerator.remove_tags_function(execution_text, self.execution_start_tag, self.execution_end_tag)
            else:
                mojo_text = execution_text
            if ProducedTextManager.draft_start_tag in mojo_text:
                self.logger.debug(f"ProducedTextManager.draft_start_tag in mojo_text")
                produced_text_manager = ProducedTextManager(self.session_id, self.user_id, user_task_execution_pk, use_draft_placeholder=use_draft_placeholder, task_name_for_system=task.name_for_system)
                produced_text, produced_text_version = produced_text_manager.extract_and_save_produced_text(
                    mojo_text, text_type_pk=task.output_text_type_fk if task else None)
                text_type = db.session.query(MdTextType.name).filter(
                    MdTextType.text_type_pk == produced_text_version.text_type_fk).first()[0]

                message = {
                    "produced_text": produced_text_version.production,
                    "produced_text_title": produced_text_version.title,
                    "produced_text_pk": produced_text.produced_text_pk,
                    "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                    "user_task_execution_pk": user_task_execution_pk,
                    "task_name": task_displayed_data.name_for_user if task_displayed_data else None,
                    "task_pk": task.task_pk if task else None,
                    "task_icon": task.icon if task else None,
                    "text_type": text_type,
                    "text_with_tags": self.execution_start_tag+mojo_text+self.execution_end_tag,
                    "text": ProducedTextManager.remove_tags(mojo_text)
                }
                return message


            else:
                self.logger.debug(f"ProducedTextManager.draft_start_tag not in mojo_text")
                return {"text": mojo_text}
        except Exception as e:
            raise Exception(f"{TaskExecutor.logger_prefix} :: manage_execution_text :: {e}")