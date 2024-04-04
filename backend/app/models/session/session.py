import os
from app import db, server_socket, time_manager, socketio_message_sender, main_logger

from models.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from mojodex_core.logging_handler import log_error
from models.session.assistant_message_generators.workflow_response_generator import WorkflowAssistantResponseGenerator
from models.session.assistant_message_generators.general_chat_response_generator import GeneralChatResponseGenerator
from models.session.assistant_message_generators.task_assistant_response_generator import TaskAssistantResponseGenerator
from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from mojodex_core.entities import *
from datetime import datetime
from models.voice_generator import VoiceGenerator
from packaging import version
from functools import wraps
from sqlalchemy.orm.attributes import flag_modified

class Session:
    logger_prefix = "Session"
    sessions_storage = "/data/users"
    mojo_messages_audios_storage_dir_name = "mojo_messages_audios"
    agent_message_key, user_message_key = "mojo", "user"



    def __init__(self, session_id):
        """
        A session is a full interaction between the user and Mojo
        :param session_id: id of the session
        """
        try:
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
        except Exception as e:
            raise Exception(f"{Session.logger_prefix} :: __init__ :: {e}")

    def __get_mojo_messages_audio_storage(self):
        """
        This private method is used to get the storage path for Mojo messages audio files.

        It first checks if the user's storage directory exists, if not, it creates it.
        Then it checks if the session's storage directory exists within the user's storage directory, if not, it creates it.
        Finally, it checks if the Mojo messages audio storage directory exists within the session's storage directory, if not, it creates it.

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
        This private method is used to get the user associated with the current session.

        It performs a database query to fetch the user whose user_id matches the user_id of the current session.
        The query joins the MdUser and MdSession tables on the user_id field and filters the results by the session_id of the current session.

        Returns:
            MdUser: The user object associated with the current session. If no user is found, it returns None.

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
        This private method is used to get the primary key of the last message sent by the user in the current session.

        It performs a database query on the MdMessage table, filtering the results by the session_id of the current session and the sender being 'user'.
        The results are then ordered by the message_date in descending order, and the first result is selected.

        Returns:
            int: The primary key of the last user message in the current session. If no message is found, it returns None.

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
            title = AssistantMessageGenerator.remove_tags_from_text(partial_text.strip(), TaskProducedTextManager.title_start_tag,
                                                    TaskProducedTextManager.title_end_tag)
            production = AssistantMessageGenerator.remove_tags_from_text(partial_text.strip(), TaskProducedTextManager.draft_start_tag,
                                                        TaskProducedTextManager.draft_end_tag)
            return {"produced_text_title": title,
                    "produced_text": production,
                    "session_id": self.id,
                    "text": TaskProducedTextManager.remove_tags(partial_text)}
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
            function: The function that manages the chat session.
        """
        app_version = version.parse(message["version"]) if "version" in message else version.parse("0.0.0")
        self.platform = message["platform"] if "platform" in message else "webapp"

        if "message_pk" not in message:
            self._new_message(message, Session.user_message_key, "user_message")

        # Home chat session here ??
        # with response_message = ...
        use_message_placeholder = "use_message_placeholder" in message and message["use_message_placeholder"]
        use_draft_placeholder = "use_draft_placeholder" in message and message["use_draft_placeholder"]

        if "origin" in message and message["origin"] == "home_chat":
            user_task_execution_pk = message['user_task_execution_pk'] if 'user_task_execution_pk' in message else None
            return self.__manage_home_chat_session(self.platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder)
        elif 'user_task_execution_pk' in message and message['user_task_execution_pk'] is not None:
            # For now only task sessions
            user_task_execution_pk = message['user_task_execution_pk']
            return self.__manage_task_session(self.platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder)
        elif 'user_workflow_execution_pk' in message and message['user_workflow_execution_pk'] is not None:
            user_workflow_execution_pk = message['user_workflow_execution_pk']
            return self.__manage_workflow_session(self.platform, user_workflow_execution_pk, use_message_placeholder, use_draft_placeholder)
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
        return self.__manage_task_session(self.platform, user_task_execution_pk, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder)

    @user_inputs_processor
    def process_workflow_step_run_rejection(self, platform, user_workflow_execution_pk, use_message_placeholder=False, use_draft_placeholder=False):
        self.platform = platform
        return self.__manage_workflow_session(platform, user_workflow_execution_pk, use_message_placeholder, use_draft_placeholder)


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
            response_message["audio"] = "text" in response_message and self.platform == "mobile" and self.voice_generator is not None
            # Does message contains a produced_text ?
            event_name = 'draft_message' if "produced_text_version_pk" in response_message else 'mojo_message'
            socketio_message_sender.send_mojo_message_with_ack(response_message, self.id, event_name = event_name)
            if response_message["audio"]:
                output_filename = os.path.join(self.__get_mojo_messages_audio_storage(), f"{message_pk}.mp3")
                try:
                    self.voice_generator.text_to_speech(response_message["text"], response_language, self.user_id, output_filename)
                except Exception as e:
                    db_message.in_error_state = datetime.now()
                    log_error(str(e), session_id=self.id)
            db_message.message = response_message
            flag_modified(db_message, "message")
            db.session.commit()
        except Exception as e:
            raise Exception(f"process_mojo_message :: {e}")

    def __manage_home_chat_session(self, platform, user_task_execution_pk, use_message_placeholder=False, use_draft_placeholder=False):
        """
        Manages a home chat session.

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
            general_chat_response_generator = GeneralChatResponseGenerator(mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                                                                              draft_token_stream_callback=self._produced_text_stream_callback,
                                                                              use_message_placeholder=use_message_placeholder,
                                                                               use_draft_placeholder=use_draft_placeholder,
                                                                               tag_proper_nouns=tag_proper_nouns,
                                                                               user=self._get_user(),
                                                                               session_id=self.id,
                                                                               user_messages_are_audio= platform=="mobile",
                                                                               running_user_task_execution_pk=user_task_execution_pk)
            response_message = general_chat_response_generator.generate_message()
            response_language = general_chat_response_generator.context.state.current_language
            return response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_home_chat_session :: {e}")

    def __manage_task_session(self, platform, user_task_execution_pk, use_message_placeholder=False, use_draft_placeholder=False):
        """
        Manages a task session.

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
            task_assistant_response_generator = TaskAssistantResponseGenerator(mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                                                                              draft_token_stream_callback=self._produced_text_stream_callback,
                                                                              use_message_placeholder=use_message_placeholder,
                                                                               use_draft_placeholder=use_draft_placeholder,
                                                                               tag_proper_nouns=tag_proper_nouns,
                                                                               user=self._get_user(),
                                                                               session_id=self.id,
                                                                               user_messages_are_audio= platform=="mobile",
                                                                               running_user_task_execution_pk=user_task_execution_pk)

            response_message = task_assistant_response_generator.generate_message()
            response_language = task_assistant_response_generator.context.state.current_language
            return response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_task_session :: {e}")


    def __manage_workflow_session(self, platform, user_workflow_execution_pk, use_message_placeholder=False, use_draft_placeholder=False):
        """
        Manages a workflow session.

        Args:
            platform (str): The platform the user is on.
            user_workflow_execution_pk (str): The primary key of the running user task execution if any
            use_message_placeholder (bool, optional): Whether to use a message placeholder. Defaults to False.
            use_draft_placeholder (bool, optional): Whether to use a draft placeholder. Defaults to False.

        Returns:
            tuple: The response message and response language.

        Raises:
            Exception: If there is an error during management.
        """
        try:
            tag_proper_nouns = platform == "mobile"
            workflow_assistant_response_generator = WorkflowAssistantResponseGenerator(mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                                                                              use_message_placeholder=use_message_placeholder,
                                                                               tag_proper_nouns=tag_proper_nouns,
                                                                               user=self._get_user(),
                                                                               session_id=self.id,
                                                                               user_messages_are_audio= platform=="mobile",
                                                                               running_user_workflow_execution_pk=user_workflow_execution_pk)

            response_message = workflow_assistant_response_generator.generate_message()
            response_language = workflow_assistant_response_generator.context.state.current_language
            return response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_workflow_session :: {e}")

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
            message = socketio_message_sender.send_error("Error during session process_chat_message: " + str(e), self.id, user_message_pk=self.__get_last_user_message_pk())
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

