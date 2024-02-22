import time

from app import db
from mojodex_core.entities import MdTextType
from models.produced_text_manager import ProducedTextManager
from mojodex_backend_logger import MojodexBackendLogger
from app import socketio_message_sender

from app import timing_logger
from packaging import version

class TaskExecutor:
    logger_prefix = "TaskExecutor::"
    execution_start_tag = "<execution>"
    execution_end_tag = "</execution>"



    def __init__(self, session_id, user_id, save_mojo_message_to_db, message_will_have_audio, generate_voice):
        self.logger = MojodexBackendLogger(f"{TaskExecutor.logger_prefix} - session_id {session_id}")
        self.session_id=session_id
        self.user_id = user_id
        self.save_mojo_message_to_db = save_mojo_message_to_db
        self.message_will_have_audio = message_will_have_audio
        self.generate_voice = generate_voice

    def manage_execution_text(
        self, execution_text, task, task_displayed_data, user_task_execution_pk, user_message, app_version, use_draft_placeholder=False):
        try:
            self.logger.debug(f"manage_execution_text")
            if self.execution_start_tag and self.execution_end_tag in execution_text:
                mojo_text = execution_text.split(self.execution_start_tag)[1].split(self.execution_end_tag)[0].strip()
            else:
                mojo_text = execution_text
            if ProducedTextManager.draft_start_tag in mojo_text:
                self.logger.debug(f"ProducedTextManager.draft_start_tag in mojo_text")
                produced_text_manager = ProducedTextManager(self.session_id, self.user_id, user_task_execution_pk, use_draft_placeholder=use_draft_placeholder, task_name_for_system=task.name_for_system)
                produced_text, produced_text_version = produced_text_manager.extract_and_save_produced_text(
                    mojo_text, text_type_pk=task.output_text_type_fk, user_message=user_message)
                text_type = db.session.query(MdTextType.name).filter(
                    MdTextType.text_type_pk == produced_text_version.text_type_fk).first()[0]

                message = {
                    "produced_text": produced_text_version.production,
                    "produced_text_title": produced_text_version.title,
                    "produced_text_pk": produced_text.produced_text_pk,
                    "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                    "user_task_execution_pk": user_task_execution_pk,
                    "task_name": task_displayed_data.name_for_user,
                    "task_pk": task.task_pk,
                    "task_icon": task.icon,
                    "text_type": text_type,
                    "text_with_tags": self.execution_start_tag+mojo_text+self.execution_end_tag,
                    "text": ProducedTextManager.remove_tags(mojo_text)
                }
                db_message = self.save_mojo_message_to_db(message, 'mojo_message')
                message["message_pk"] = db_message.message_pk
                message["audio"] = self.message_will_have_audio(message)
               
                socketio_message_sender.send_mojo_message_with_ack(message, self.session_id, event_name='draft_message')
                if message["audio"]:
                    self.generate_voice(db_message)


            else:
                self.logger.debug(f"ProducedTextManager.draft_start_tag not in mojo_text")
                return {"text": mojo_text}
        except Exception as e:
            raise Exception(f"{TaskExecutor.logger_prefix} :: manage_execution_text :: {e}")