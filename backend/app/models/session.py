import os
import requests
from app import db, log_error, server_socket, executor, time_manager, socketio_message_sender, main_logger
from mojodex_core.entities import *
from datetime import datetime
from models.voice_generator import VoiceGenerator
from models.tasks.task_manager import TaskManager
from packaging import version
from functools import wraps

from models.home_chat.home_chat_manager import HomeChatManager


class Session:
    logger_prefix = "Session"
    sessions_storage = "/data/users"
    agent_message_key, user_message_key = "mojo", "user"

    def __init__(self, session_id):
        """
        A session is a full interaction between the user and Mojo
        :param session_id: id of the session
        """
        self.id = session_id
        user = self._get_user()
        self.user_id = user.user_id
        self.platform = None
        if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
            try:
                self.voice_generator = VoiceGenerator()
            except Exception as e:
                self.voice_generator = None
                main_logger.error(f"{Session.logger_prefix}:: Can't initialize voice generator")
        else:
            self.voice_generator = None

    def __get_mojo_messages_audio_storage(self):
        try:
            user_storage = os.path.join(Session.sessions_storage, self.user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage, exist_ok=True)
            session_storage = os.path.join(user_storage, self.id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage, exist_ok=True)
            mojo_messages_audio_storage = os.path.join(session_storage, "mojo_messages_audios")
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)
            return mojo_messages_audio_storage
        except Exception as e:
            raise Exception(f"__get_mojo_messages_audio_storage :: {e}")

    def _get_user(self):
        return db.session.query(MdUser).join(MdSession, MdSession.user_id == MdUser.user_id).filter(
            MdSession.session_id == self.id).first()

        return db.session.query(MdMessage).filter(MdMessage.session_id == self.id).count()

    def __get_last_user_message(self):
        try:
            last_user_message_pk = db.session.query(MdMessage.message_pk) \
                .filter(MdMessage.session_id == self.id) \
                .filter(MdMessage.sender == 'user') \
                .order_by(MdMessage.message_date.desc()).first()
            if last_user_message_pk is None:
                return None
            return last_user_message_pk[0] if last_user_message_pk else None
        except Exception as e:
            raise Exception(f"__get_last_user_message :: {e}")

    def _mojo_message_stream_callback(self, partial_text):
        try:
            server_socket.emit('mojo_token', {"text": partial_text, 'session_id': self.id}, to=self.id)
        except Exception as e:
            raise Exception(f"_mojo_token_callback :: {e}")

    def set_produced_text_version_read_by_user(self, produced_text_version_pk):
        produced_text_version = db.session.query(MdProducedTextVersion).filter(
            MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk).first()
        produced_text_version.read_by_user = datetime.now()
        db.session.commit()

    def set_mojo_message_read_by_user(self, message_pk):
        try:
            mojo_message = db.session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
            mojo_message.read_by_user = datetime.now()
            # check if there is a produced_text_version_pk in the message
            if "produced_text_version_pk" in mojo_message.message:
                produced_text_version_pk = mojo_message.message["produced_text_version_pk"]
                self.set_produced_text_version_read_by_user(produced_text_version_pk)
            db.session.commit()
        except Exception as e:
            log_error("Error during set_mojo_message_read_by_user: " + str(e))

    def user_inputs_processor(generate_mojo_message_func):
        """
        Decorator function to process user inputs. It wraps around the function that generates mojo's message, 
        processes the message and handles any exceptions that occur during this process.

        Args:
            generate_message_func (function): The function that generates the message.

        Returns:
            function: The wrapped function.
        """
        @wraps(generate_mojo_message_func)
        def wrapper(self, *args, **kwargs):
            try:
                response_event_name, response_message, response_language = generate_mojo_message_func(self, *args, **kwargs)
                if response_message:
                    self.process_mojo_message(response_event_name, response_message, response_language)
                db.session.close()
            except Exception as e:
                self.__process_error_during_message_generation(e)
        return wrapper

    @user_inputs_processor
    def process_chat_message(self, message):
        """
        Processes a chat message received from the user.

        Args:
            message (dict): The message from the user.

        Returns:
            function: The function that manages the chat session.
        """
        app_version = version.parse(message["version"]) if "version" in message else version.parse("0.0.0")
        self.platform = message["platform"] if "platform" in message else "webapp"

        if "message_pk" not in message:
            self._new_message(message, Session.user_message_key, "user_message")

        # Home chat session here ??
        # with response_message = ...
        if "origin" in message and message["origin"] == "home_chat":
            return self.__manage_home_chat_session(message, app_version, self.platform)
        elif 'user_task_execution_pk' in message:
            # For now only task sessions
            user_task_execution_pk = message['user_task_execution_pk']
            return self.__manage_task_session(app_version, self.platform, user_task_execution_pk, user_message=message)
        else:
            raise Exception("Unknown message origin")

    
    @user_inputs_processor
    def process_form_input(self, app_version, platform, user_task_execution_pk, use_message_placeholder=False, use_draft_placeholder=False):
        """
        Processes a form input from the user.

        Args:
            app_version (str): The version of the app.
            platform (str): The platform the user is on (webapp, mobile, etc.).
            user_task_execution_pk (str): The primary key of the user task execution started by the form.
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            function: The function that manages the task session.
        """
        self.platform = platform
        return self.__manage_task_session(app_version, self.platform, user_task_execution_pk, user_message=None, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder)

    def process_mojo_message(self, response_event_name, response_message, response_language):
        """
        Processes a mojo message.

        Args:
            response_event_name (str): The name of the response event.
            response_message (dict): The response message.
            response_language (str): The language of the response.

        Raises:
            Exception: If there is an error during processing.
        """
        try:
            if "session_id" not in response_message:
                response_message["session_id"] = self.id
            db_message = self._new_message(response_message, Session.agent_message_key, response_event_name)
            message_pk = db_message.message_pk
            response_message["message_pk"] = message_pk
            response_message["audio"] = "text" in response_message and self.platform == "mobile" and self.voice_generator is not None
            if response_event_name == 'mojo_message': # TODO: Is it session's responsibility to send message that are not mojo_message (e.g. draft_message) ?
                socketio_message_sender.send_mojo_message_with_ack(response_message, self.id)
            else:
                server_socket.emit(response_event_name, response_message, to=self.id)
            if response_message["audio"]:
                output_filename = os.path.join(self.__get_mojo_messages_audio_storage(), f"{message_pk}.mp3")
                try:
                    self.voice_generator.text_to_speech(response_message["text"], response_language, self.user_id, output_filename)
                except Exception as e:
                    db_message.in_error_state = datetime.now()
                    log_error(str(e), session_id=self.id)
        except Exception as e:
            raise Exception(f"process_mojo_message :: {e}")

    def __manage_home_chat_session(self, message, app_version, platform):
        """
        Manages a home chat session.

        Args:
            message (dict): The message from the user.
            app_version (str): The version of the app.
            platform (str): The platform the user is on.

        Returns:
            tuple: The response event name, response message, and response language.

        Raises:
            Exception: If there is an error during management.
        """
        try:
            home_chat_manager = HomeChatManager(session_id=self.id, user=self._get_user(), platform=platform, app_version=app_version,
                                                 voice_generator=self.voice_generator, mojo_messages_audio_storage=self.__get_mojo_messages_audio_storage(), mojo_token_callback=self._mojo_message_stream_callback)
            response_event_name, response_message, response_language = home_chat_manager.launch_mojo_message_generation(user_message=message)
            return response_event_name, response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_home_chat_session :: {e}")

    def __manage_task_session(self, app_version, platform, user_task_execution_pk, user_message=None, use_message_placeholder=False, use_draft_placeholder=False):
        """
        Manages a task session.

        Args:
            app_version (str): The version of the app.
            platform (str): The platform the user is on.
            user_task_execution_pk (str): The primary key of the user task execution.
            user_message (dict, optional): The message from the user. Defaults to None.
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            tuple: The response event name, response message, and response language.

        Raises:
            Exception: If there is an error during management.
        """
        try:
            task_manager = TaskManager(self._get_user(), self.id, platform, app_version, self.voice_generator, self.__get_mojo_messages_audio_storage(),  
                                       mojo_token_callback=self._mojo_message_stream_callback, user_task_execution_pk=user_task_execution_pk)
            tag_proper_nouns = platform == "mobile"
            response_event_name, response_message, response_language = task_manager.launch_mojo_message_generation(user_message=user_message, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder, tag_proper_nouns=tag_proper_nouns)

            return response_event_name, response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_task_session :: {e}")

    def __process_error_during_message_generation(self, e):
        """
        Processes an error that occurs during message generation.

        Args:
            e (Exception): The exception that occurred.

        Returns:
            None
        """
        try:
            db.session.rollback()
            message = socketio_message_sender.send_error("Error during session process_chat_message: " + str(e), self.id, user_message_pk=self.__get_last_user_message())
            self._new_message(message, Session.agent_message_key, 'error')
            db.session.close()
        except Exception as e:
            db.session.close()

    def _new_message(self, message, sender, event_name):
        """
        Save message in DB
        :param message: Message to save
        :param sender: Who sent the message
        :return:
        """
        try:
            if sender == Session.user_message_key:
                message_date = message["message_date"]
                timezone_offset = int(message["timezone_offset"])
                message_date = time_manager.device_date_to_backend_date(message_date, timezone_offset)
            else:
                message_date = datetime.now()
            message = MdMessage(session_id=self.id, sender=sender, event_name=event_name, message=message,
                                creation_date=datetime.now(), message_date=message_date)
            db.session.add(message)
            db.session.commit()
            return message
        except Exception as e:
            db.session.rollback()
            raise Exception(f"new_message : {e}")

