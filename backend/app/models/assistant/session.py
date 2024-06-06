import os

import requests
from app import db, server_socket, time_manager, socketio_message_sender, main_logger
from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from models.assistant.instruct_task_assistant import InstructTaskAssistant
from models.assistant.home_chat_assistant import HomeChatAssistant

from models.assistant.chat_assistant import ChatAssistant

from models.assistant.models.instruct_task_execution import InstructTaskExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from datetime import datetime
from models.voice_generator import VoiceGenerator
from packaging import version
from functools import wraps
from sqlalchemy.orm.attributes import flag_modified
from mojodex_core.db import engine
from mojodex_core.db import Session as DbSession

class Session:
    sessions_storage = "/data/users"
    mojo_messages_audios_storage_dir_name = "mojo_messages_audios"
    agent_message_key, user_message_key = "mojo", "user"

    def __init__(self, session_id):
        """
        A assistant is a full interaction between the user and Mojo
        :param session_id: id of the assistant
        """
        try:
            self.id = session_id
            user = self._get_user()
            self.user_id = user.user_id

            self.db_session = DbSession(engine)
            self.platform = None
            if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
                try:
                    self.voice_generator = VoiceGenerator()
                except Exception as e:
                    self.voice_generator = None
                    main_logger.error(f"{self.__class__.__name__}:: Can't initialize voice generator")
            else:
                self.voice_generator = None
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: __init__ :: {e}")

    def __get_mojo_messages_audio_storage(self):
        """
        This private method is used to get the storage path for Mojo messages audio files.

        It first checks if the user's storage directory exists, if not, it creates it.
        Then it checks if the assistant's storage directory exists within the user's storage directory, if not, it creates it.
        Finally, it checks if the Mojo messages audio storage directory exists within the assistant's storage directory, if not, it creates it.

        Returns:
            str: The path to the Mojo messages audio storage directory.

        Raises:
            Exception: If any error occurs while checking for or creating the directories.
        """
        try:
            user_storage = os.path.join(Session.sessions_storage, self.user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage, exist_ok=True)
            session_storage = os.path.join(user_storage, self.id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage, exist_ok=True)
            mojo_messages_audio_storage = os.path.join(session_storage, Session.mojo_messages_audios_storage_dir_name)
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)
            return mojo_messages_audio_storage
        except Exception as e:
            raise Exception(f"__get_mojo_messages_audio_storage :: {e}")

    def _get_user(self):
        """
        This private method is used to get the user associated with the current assistant.

        It performs a database query to fetch the user whose user_id matches the user_id of the current assistant.
        The query joins the MdUser and MdSession tables on the user_id field and filters the results by the session_id of the current assistant.

        Returns:
            MdUser: The user object associated with the current assistant. If no user is found, it returns None.

        Raises:
            Exception: If any error occurs while querying the database.
        """
        try:
            return db.session.query(MdUser).join(MdSession, MdSession.user_id == MdUser.user_id).filter(
                MdSession.session_id == self.id).first()
        except Exception as e:
            raise Exception(f"_get_user :: {e}")

    def __get_last_user_message_pk(self):
        """
        This private method is used to get the primary key of the last message sent by the user in the current assistant.

        It performs a database query on the MdMessage table, filtering the results by the session_id of the current assistant and the sender being 'user'.
        The results are then ordered by the message_date in descending order, and the first result is selected.

        Returns:
            int: The primary key of the last user message in the current assistant. If no message is found, it returns None.

        Raises:
            Exception: If any error occurs while performing the database query.
        """
        try:
            last_user_message_pk = db.session.query(MdMessage.message_pk) \
                .filter(MdMessage.session_id == self.id) \
                .filter(MdMessage.sender == 'user') \
                .order_by(MdMessage.message_date.desc()).first()
            if last_user_message_pk is None:
                return None
            return last_user_message_pk[0] if last_user_message_pk else None
        except Exception as e:
            raise Exception(f"__get_last_user_message_pk :: {e}")

    ### STREAM CALLBACKS ###
    def token_stream_callback(event_name):
        """
        Decorator function to process token stream callbacks. It wraps around the function that processes the token stream,
        processes the token stream and handles any exceptions that occur during this process.

        Args:
            event_name (str): The event name to be emitted.

        Returns:
            function: The wrapped function.
        """

        def decorator(stream_callback_func):
            @wraps(stream_callback_func)
            def wrapper(self, partial_text):
                try:
                    message = stream_callback_func(self, partial_text)
                    server_socket.emit(event_name, message, to=self.id)
                except Exception as e:
                    raise Exception(f"token_stream_callback :: {e}")

            return wrapper

        return decorator

    @token_stream_callback('mojo_token')
    def _mojo_message_stream_callback(self, partial_text):
        try:
            return {"text": partial_text, 'session_id': self.id}
        except Exception as e:
            raise Exception(f"_mojo_message_stream_callback :: {e}")

    @token_stream_callback('draft_token')
    def _produced_text_stream_callback(self, partial_text):
        try:
            title = ChatAssistant.remove_tags_from_text(partial_text.strip(),
                                                        InstructTaskProducedTextManager.title_start_tag,
                                                        InstructTaskProducedTextManager.title_end_tag)
            production = ChatAssistant.remove_tags_from_text(partial_text.strip(),
                                                             InstructTaskProducedTextManager.draft_start_tag,
                                                             InstructTaskProducedTextManager.draft_end_tag)
            return {"produced_text_title": title,
                    "produced_text": production,
                    "session_id": self.id,
                    "text": InstructTaskProducedTextManager.remove_tags(partial_text)}
        except Exception as e:
            raise Exception(f"_produced_text_stream_callback :: {e}")

    ### STREAM ACKNOWLEDGEMENTS ###
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

    ### PROCESS MESSAGE ###
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
                response_message, response_language = generate_mojo_message_func(self, *args, **kwargs)
                if response_message:
                    self.process_mojo_message(response_message, response_language)
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
            function: The function that manages the chat assistant.
        """
        app_version = version.parse(message["version"]) if "version" in message else version.parse("0.0.0")
        self.platform = message["platform"] if "platform" in message else "webapp"

        if "message_pk" not in message:
            self._new_message(message, Session.user_message_key, "user_message")

        instruct_task_execution = None
        # if "user_task_execution_pk" in message and message["user_task_execution_pk"] is not None, let's update task title and summary
        if "user_task_execution_pk" in message and message["user_task_execution_pk"] is not None:
            user_task_execution_pk = message["user_task_execution_pk"]
            instruct_task_execution = InstructTaskExecution(user_task_execution_pk, self.db_session)
            instruct_task_execution.generate_title_and_summary()
            #server_socket.start_background_task(self._give_task_execution_title_and_summary, user_task_execution_pk)

        # Home chat assistant here ??
        # with response_message = ...
        use_message_placeholder = "use_message_placeholder" in message and message["use_message_placeholder"]
        use_draft_placeholder = "use_draft_placeholder" in message and message["use_draft_placeholder"]

        if "origin" in message and message["origin"] == "home_chat":
            return self.__manage_home_chat_session(self.platform, instruct_task_execution, use_message_placeholder)

        elif 'user_task_execution_pk' in message and message['user_task_execution_pk'] is not None:
            # For now only task sessions
            return self.__manage_task_session(self.platform, instruct_task_execution, use_message_placeholder,
                                              use_draft_placeholder)
        else:
            raise Exception("Unknown message origin")

    def _give_task_execution_title_and_summary(self, user_task_execution_pk):
        try:
            # call background backend /end_user_task_execution to update user task execution title and summary
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/user_task_execution_title_and_summary"
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_pk': user_task_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background user_task_execution_title_and_summary : {internal_request.json()}")
        except Exception as e:
            print(f"🔴 __give_title_and_summary_task_execution :: {e}")

    @user_inputs_processor
    def process_form_input(self, app_version, platform, user_task_execution_pk, use_message_placeholder=False,
                           use_draft_placeholder=False):
        """
        Processes a form input from the user.

        Args:
            app_version (str): The version of the app.
            platform (str): The platform the user is on (webapp, mobile, etc.).
            user_task_execution_pk (str): The primary key of the user task execution started by the form.
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            function: The function that manages the task assistant.
        """
        instruct_task_execution = InstructTaskExecution(user_task_execution_pk, self.db_session)
        instruct_task_execution.generate_title_and_summary()
        #server_socket.start_background_task(self._give_task_execution_title_and_summary, user_task_execution_pk)

        self.platform = platform
        return self.__manage_instruct_task_session(self.platform, instruct_task_execution,
                                                   use_message_placeholder=use_message_placeholder,
                                                   use_draft_placeholder=use_draft_placeholder)

    def process_mojo_message(self, response_message, response_language):
        """
        Processes a mojo message.

        Args:
            response_message (dict): The response message.
            response_language (str): The language of the response.

        Raises:
            Exception: If there is an error during processing.
        """
        try:
            # Ensure that the message has a session_id
            if "session_id" not in response_message:
                response_message["session_id"] = self.id
            # Save message in DB as mojo_message
            db_message = self._new_message(response_message, Session.agent_message_key, "mojo_message")
            message_pk = db_message.message_pk
            response_message["message_pk"] = message_pk
            response_message[
                "audio"] = "text" in response_message and self.platform == "mobile" and self.voice_generator is not None
            # Does message contains a produced_text ?
            event_name = 'draft_message' if "produced_text_version_pk" in response_message else 'mojo_message'
            socketio_message_sender.send_mojo_message_with_ack(response_message, self.id, event_name=event_name)
            if response_message["audio"]:
                output_filename = os.path.join(self.__get_mojo_messages_audio_storage(), f"{message_pk}.mp3")
                try:
                    self.voice_generator.text_to_speech(response_message["text"], response_language, self.user_id,
                                                        output_filename)
                except Exception as e:
                    db_message.in_error_state = datetime.now()
                    log_error(str(e), session_id=self.id)
            db_message.message = response_message
            flag_modified(db_message, "message")
            db.session.commit()
        except Exception as e:
            raise Exception(f"process_mojo_message :: {e}")

    def __manage_home_chat_session(self, platform: str, instruct_task_execution: InstructTaskExecution, use_message_placeholder: bool =False):
        """
        Manages a home chat assistant.

        Args:
            platform (str): The platform the user is on.
            user_task_execution_pk (str): The primary key of the running user task execution if any
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            tuple: The response message and response language.

        Raises:
            Exception: If there is an error during management.
        """
        try:
            tag_proper_nouns = platform == "mobile"
            user_messages_are_audio = platform == "mobile"
            home_chat_assistant = HomeChatAssistant(
                mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                draft_token_stream_callback=self._produced_text_stream_callback,
                use_message_placeholder=use_message_placeholder,
                user_id=self.user_id,
                session_id=self.id,
                tag_proper_nouns=tag_proper_nouns,
                user_messages_are_audio=user_messages_are_audio,
                running_user_task_execution=instruct_task_execution,
                db_session=self.db_session
            )
            response_message = home_chat_assistant.generate_message()
            response_language = home_chat_assistant.language
            return response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_home_chat_session :: {e}")

    def __manage_task_session(self, platform: str, instruct_task_execution: InstructTaskExecution, use_message_placeholder: bool = False,
                              use_draft_placeholder: bool = False):
        try:
            # What is the task type ?
            db_task = db.session.query(MdTask) \
                .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == instruct_task_execution.user_task_execution_pk) \
                .first()
            if db_task is None:
                raise Exception(f"Task of user_task_execution {instruct_task_execution.user_task_execution_pk} not found")
            if db_task.type == "instruct":
                return self.__manage_instruct_task_session(platform, instruct_task_execution, use_message_placeholder,
                                                           use_draft_placeholder)
            else:
                raise Exception(f"Can't chat with task of type {db_task.type}")
        except Exception as e:
            raise Exception(f"__manage_task_session :: {e}")

    def __manage_instruct_task_session(self, platform: str, instruct_task_execution: InstructTaskExecution, use_message_placeholder: bool = False,
                                       use_draft_placeholder: bool = False):
        """
        Manages a task assistant.

        Args:
            platform (str): The platform the user is on.
            user_task_execution_pk (str): The primary key of the running user task execution if any
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            tuple: The response message and response language.

        Raises:
            Exception: If there is an error during management.
        """
        try:
            tag_proper_nouns = platform == "mobile"
            user_messages_are_audio = platform == "mobile"
            instruct_task_assistant = InstructTaskAssistant(
                mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                draft_token_stream_callback=self._produced_text_stream_callback,
                use_message_placeholder=use_message_placeholder,
                use_draft_placeholder=use_draft_placeholder,
                tag_proper_nouns=tag_proper_nouns,
                user_messages_are_audio=user_messages_are_audio,
                running_user_task_execution=instruct_task_execution)

            response_message = instruct_task_assistant.generate_message()
            response_language = instruct_task_assistant.language
            return response_message, response_language
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
            message = socketio_message_sender.send_error("Error during assistant process_chat_message: " + str(e),
                                                         self.id, user_message_pk=self.__get_last_user_message_pk())
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
