import os
from datetime import datetime
from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator

from mojodex_core.entities import *
from app import db, log_error, server_socket, main_logger, socketio_message_sender

from models.session.session import Session
from models.voice_generator import VoiceGenerator
from models.tasks.task_executor import TaskExecutor
from models.produced_text_manager import ProducedTextManager

from app import llm, llm_conf, llm_backup_conf


class TextEditActionManager:
    logger_prefix = "TextEditActionManager"

    text_edit_executor = llm(llm_conf, label="TEXT_EDIT_EXECUTOR",
                                       llm_backup_conf=llm_backup_conf)

    def __init__(
            self,
            user_id,
            language,
            task_name_for_system,
            session_id,
            user_task_execution_pk,
            produced_text_fk,
            text_type_fk,
            user_message_pk,
            platform):
        self.user_id = user_id
        self.language = language
        self.task_name_for_system = task_name_for_system
        self.session_id = session_id
        self.user_task_execution_pk = user_task_execution_pk
        self.produced_text_fk = produced_text_fk
        self.text_type_fk = text_type_fk
        self.platform = platform
        self.user_message_pk = user_message_pk
        if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
            try:
                self.voice_generator = VoiceGenerator()
            except Exception as e:
                self.voice_generator = None
                main_logger.error(
                    f"{TextEditActionManager.logger_prefix}:: Can't initialize voice generator")
        else:
            self.voice_generator = None

    def edit_text(self, input_prompt, app_version):
        # Edit text
        try:
            edited_text = TextEditActionManager.text_edit_executor.invoke(
                messages=[{"role": "system", "content": input_prompt}],
                user_id=self.user_id,
                temperature=0.3,
                max_tokens=2000,
                stream=True,
                stream_callback=lambda stream_output_text: self.__send_draft_token(
                    token_text=stream_output_text),
                user_task_execution_pk=self.user_task_execution_pk,
                task_name_for_system=self.task_name_for_system
            )[0]  # Because chat returns a list

            event_name = "draft_message"
            draft_message = {
                "produced_text_pk": self.produced_text_fk,
                "produced_text_title": self.__get_title_without_tags(edited_text),
                "produced_text": self.__get_draft_without_tags(edited_text),
                "text": self.__get_text_without_tags(edited_text),
                "text_with_tags": TaskExecutor.execution_start_tag + edited_text + TaskExecutor.execution_end_tag
            }

            title = self.__get_title_without_tags(edited_text)
            production = self.__get_draft_without_tags(edited_text)
            embedding = ProducedTextManager.embed_produced_text(title, production, self.user_id,
                                                                user_task_execution_pk=self.user_task_execution_pk,
                                                                task_name_for_system=self.task_name_for_system)
            # Save produced text version to db
            new_produced_text_version = MdProducedTextVersion(
                creation_date=datetime.now(),
                production=production,
                produced_text_fk=self.produced_text_fk,
                title=title,
                text_type_fk=self.text_type_fk,
                embedding=embedding
            )
            # Add the new produced text version pk to the message saved in db
            db.session.add(new_produced_text_version)
            db.session.flush()
            draft_message["produced_text_version_pk"] = new_produced_text_version.produced_text_version_pk

            # Save message to db
            db_message = MdMessage(
                session_id=self.session_id,
                sender='mojo',
                event_name=event_name,
                message=draft_message,
                creation_date=datetime.now(),
                message_date=datetime.now())
            db.session.add(db_message)
            db.session.flush()
            draft_message["message_pk"] = db_message.message_pk

            db.session.commit()

            draft_message["audio"] = "text" in draft_message and self.platform == "mobile" and self.voice_generator

            # Send message to frontend
            socketio_message_sender.send_mojo_message_with_ack(
                message=draft_message,
                session_id=self.session_id,
                event_name="draft_message"
            )

            # Generate audio
            if draft_message["audio"]:
                self.__text_to_speech(draft_message, db_message)

            db.session.close()

        except Exception as e:
            db.session.close()
            socketio_message_sender.send_error(f"Error running text edit action: {e}", self.session_id,
                                               user_message_pk=self.user_message_pk)

    def __send_draft_token(self, token_text):

        try:
            produced_text_title = self.__get_title_without_tags(token_text)

            produced_text = self.__get_draft_without_tags(token_text)

            text = self.__get_text_without_tags(token_text)

            server_socket.emit(
                "draft_token",
                {"produced_text_title": produced_text_title,
                 "produced_text": produced_text,
                 "session_id": self.session_id,
                 "text": text
                 },
                to=self.session_id,
            )
        except Exception as e:
            raise Exception(f"__send_draft_token :: {e}")

    def __get_title_without_tags(self, edited_text):
        try:
            return AssistantMessageGenerator.remove_tags_from_text(
                text=edited_text.strip(),
                start_tag=ProducedTextManager.title_start_tag,
                end_tag=ProducedTextManager.title_end_tag
            )
        except Exception as e:
            raise Exception(f"__get_title_without_tags :: {e}")

    def __get_draft_without_tags(self, edited_text):
        try:
            return AssistantMessageGenerator.remove_tags_from_text(
                text=edited_text.strip(),
                start_tag=ProducedTextManager.draft_start_tag,
                end_tag=ProducedTextManager.draft_end_tag
            )
        except Exception as e:
            raise Exception(f"__get_draft_without_tags :: {e}")

    def __get_text_without_tags(self, edited_text):
        try:
            return ProducedTextManager.remove_tags(edited_text.strip())
        except Exception as e:
            raise Exception(f"__get_text_without_tags :: {e}")

    def __text_to_speech(self, message, db_message):

        try:
            # Check if the user has a folder to store the audio and create it if not
            user_storage = os.path.join(Session.sessions_storage, self.user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage, exist_ok=True)
            session_storage = os.path.join(user_storage, self.session_id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage, exist_ok=True)
            mojo_messages_audio_storage = os.path.join(
                session_storage, "mojo_messages_audios")
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)

            # Define the output filename
            output_filename = os.path.join(
                mojo_messages_audio_storage, f"{message['message_pk']}.mp3")

            # Generate audio
            self.voice_generator.text_to_speech(
                text=message["text"],
                language_code=self.language,
                user_id=self.user_id,
                output_filename=output_filename,
                user_task_execution_pk=self.user_task_execution_pk,
                task_name_for_system=self.task_name_for_system
            )

        except Exception as e:
            db_message.in_error_state = datetime.now()
            log_error(f"{TextEditActionManager.logger_prefix} :: __text_to_speech : {str(e)}",
                      session_id=self.session_id, notify_admin=True)
