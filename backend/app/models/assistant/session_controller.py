import os
from app import server_socket, socketio_message_sender, main_logger
from mojodex_core.tag_manager import TagManager
from mojodex_core.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from models.assistant.instruct_task_assistant import InstructTaskAssistant
from models.assistant.home_chat_assistant import HomeChatAssistant
from models.assistant.workflow_assistant import WorkflowAssistant
from mojodex_core.entities.instruct_user_task_execution import InstructTaskExecution
from mojodex_core.entities.message import Message
from mojodex_core.entities.session import Session
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdProducedTextVersion, MdUserTask, MdTask, MdUserTaskExecution
from models.voice_generator import VoiceGenerator
from packaging import version
from functools import wraps
from sqlalchemy.orm.attributes import flag_modified
from mojodex_core.db import MojodexCoreDB
from mojodex_core.db import Session as DbSession
from mojodex_core.task_execution_title_summary_generator import TaskExecutionTitleSummaryGenerator
from mojodex_core.timezone_service import device_date_to_backend_date
from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager
from datetime import datetime

class SessionController:

    def __del__(self):
        self.db_session.close()

    def __init__(self, session_id):
        """
        A SessionController is responsible to manage chat interactions between the user and Mojo.
        A session representes a full interaction between the user and Mojo.
        :param session_id: id of the managed session.
        """
        try:
            self.db_session = DbSession(MojodexCoreDB().engine)
            self.session = self.db_session.query(Session).get(session_id)
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
                    server_socket.emit(event_name, message, to=self.session.session_id)
                except Exception as e:
                    raise Exception(f"token_stream_callback :: {e}")

            return wrapper

        return decorator

    @token_stream_callback('mojo_token')
    def _mojo_message_stream_callback(self, partial_text):
        try:
            return {"text": partial_text, 'session_id': self.session.session_id}
        except Exception as e:
            raise Exception(f"_mojo_message_stream_callback :: {e}")

    @token_stream_callback('draft_token')
    def _produced_text_stream_callback(self, partial_text):
        try:
            title_tag_manager = TagManager("title")
            draft_tag_manager = TagManager("draft")
            title = title_tag_manager.extract_text(partial_text.strip())
            production = draft_tag_manager.extract_text(partial_text.strip())
            return {"produced_text_title": title,
                    "produced_text": production,
                    "session_id": self.session.session_id,
                    "text": TaskProducedTextManager.get_produced_text_without_tags(partial_text)}
        except Exception as e:
            raise Exception(f"_produced_text_stream_callback :: {e}")

    ### STREAM ACKNOWLEDGEMENTS ###
    def set_produced_text_version_read_by_user(self, produced_text_version_pk):
        produced_text_version = self.db_session.query(MdProducedTextVersion).filter(
            MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk).first()
        produced_text_version.read_by_user = datetime.now()
        self.db_session.commit()

    def set_mojo_message_read_by_user(self, message_pk):
        try:
            mojo_message = self.db_session.query(Message).get(message_pk)
            mojo_message.read_by_user = datetime.now()
            # check if there is a produced_text_version_pk in the message
            if "produced_text_version_pk" in mojo_message.message:
                produced_text_version_pk = mojo_message.message["produced_text_version_pk"]
                self.set_produced_text_version_read_by_user(produced_text_version_pk)
            self.db_session.commit()
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
            self._new_message(message, Message.user_message_key, "user_message")

        user_task_execution = None
        # if "user_task_execution_pk" in message and message["user_task_execution_pk"] is not None, let's update task title and summary
        if "user_task_execution_pk" in message and message["user_task_execution_pk"] is not None:
            user_task_execution_pk = message["user_task_execution_pk"]
            user_task_execution = self._get_user_task_execution_entity(user_task_execution_pk)
            # Check if the task has a title to create one if necessary
            if user_task_execution.title is None:
                # a lambda function to provide to the generate_title_and_summary function to emit the title to the front
                callback = lambda title, summary: server_socket.emit('user_task_execution_title',
                                                                    {"title": title, "session_id": user_task_execution.session_id},
                                                                    to=user_task_execution.session_id)

                server_socket.start_background_task(TaskExecutionTitleSummaryGenerator.generate_title_and_summary,
                                                    user_task_execution.user_task_execution_pk, callback=callback)

        # Home chat assistant here ??
        # with response_message = ...
        use_message_placeholder = "use_message_placeholder" in message and message["use_message_placeholder"]
        use_draft_placeholder = "use_draft_placeholder" in message and message["use_draft_placeholder"]

        if "origin" in message and message["origin"] == "home_chat":
            return self.__manage_home_chat_session(self.platform, user_task_execution, use_message_placeholder)

        elif 'user_task_execution_pk' in message and message['user_task_execution_pk'] is not None:
            # For now only task sessions
            if user_task_execution.task.type == "instruct":
                return self.__manage_instruct_task_session(self.platform, user_task_execution, use_message_placeholder,
                                                           use_draft_placeholder)
            else:
                return self.__manage_workflow_session(self.platform, user_task_execution, use_message_placeholder,
                                                      use_draft_placeholder)
        else:
            raise Exception("Unknown message origin")

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
        instruct_task_execution = self.db_session.query(InstructTaskExecution).get(user_task_execution_pk)
        # Check if the task has a title to create one if necessary
        if instruct_task_execution.title is None:
            # a lambda function to provide to the generate_title_and_summary function to emit the title to the front
            callback = lambda title, summary: server_socket.emit('user_task_execution_title',
                                                                {"title": title, "session_id": instruct_task_execution.session_id},
                                                                to=instruct_task_execution.session_id)
            server_socket.start_background_task(TaskExecutionTitleSummaryGenerator.generate_title_and_summary,
                                                instruct_task_execution.user_task_execution_pk, callback=callback)

        self.platform = platform
        return self.__manage_instruct_task_session(self.platform, instruct_task_execution,
                                                   use_message_placeholder=use_message_placeholder,
                                                   use_draft_placeholder=use_draft_placeholder)

    def _get_user_task_execution_entity(self, user_task_execution_pk):
        try:
            type = self.db_session.query(MdTask.type) \
                .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .first()[0]
            if type == "instruct":
                return self.db_session.query(InstructTaskExecution).get(user_task_execution_pk)
            elif type == "workflow":
                return self.db_session.query(UserWorkflowExecution).get(user_task_execution_pk)
            else:
                raise Exception(f"Unknown task type {type}")
        except Exception as e:
            raise Exception(f"_get_user_task_execution_entity :: {e}")

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
                response_message["session_id"] = self.session.session_id
            # Save message in DB as mojo_message
            db_message = self._new_message(response_message, Message.agent_message_key, "mojo_message")
            message_pk = db_message.message_pk
            response_message["message_pk"] = message_pk
            response_message[
                "audio"] = "text" in response_message and self.platform == "mobile" and self.voice_generator is not None
            # Does message contains a produced_text ?
            event_name = 'draft_message' if "produced_text_version_pk" in response_message else 'mojo_message'
            socketio_message_sender.send_mojo_message_with_ack(response_message, self.session.session_id,
                                                               event_name=event_name)
            if response_message["audio"]:
                output_filename = os.path.join(
                    UserAudioFileManager().get_mojo_messages_audio_storage(self.session.user_id,
                                                                            self.session.session_id),
                    f"{message_pk}.mp3")
                try:
                    self.voice_generator.text_to_speech(response_message["text"], response_language,
                                                        self.session.user_id,
                                                        output_filename)
                except Exception as e:
                    db_message.in_error_state = datetime.now()
                    log_error(str(e), session_id=self.session.session_id)
            db_message.message = response_message
            flag_modified(db_message, "message")
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"process_mojo_message :: {e}")

    def __manage_home_chat_session(self, platform: str, instruct_task_execution: InstructTaskExecution,
                                   use_message_placeholder: bool = False):
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
                user_id=self.session.user_id,
                session_id=self.session.session_id,
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

    def __manage_instruct_task_session(self, platform: str, instruct_task_execution: InstructTaskExecution,
                                       use_message_placeholder: bool = False,
                                       use_draft_placeholder: bool = False):
        """
        Manages an instruct task assistant.

        Args:
            platform (str): The platform the user is on.
            instruct_task_execution (InstructTaskExecution): The running user task execution.
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
                running_user_task_execution=instruct_task_execution,
                db_session=self.db_session)

            response_message = instruct_task_assistant.generate_message()
            response_language = instruct_task_assistant.language
            return response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_instruct_task_session :: {e}")

    def __manage_workflow_session(self, platform: str, workflow_execution: UserWorkflowExecution,
                                  use_message_placeholder: bool = False,
                                  use_draft_placeholder: bool = False):
        """
        Manages a workflow assistant.

        Args:
            platform (str): The platform the user is on.
            workflow_execution (UserWorkflowExecution): The running user task execution.
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
            workflow_assistant = WorkflowAssistant(
                mojo_message_token_stream_callback=self._mojo_message_stream_callback,
                draft_token_stream_callback=self._produced_text_stream_callback,
                use_message_placeholder=use_message_placeholder,
                use_draft_placeholder=use_draft_placeholder,
                tag_proper_nouns=tag_proper_nouns,
                user_messages_are_audio=user_messages_are_audio,
                running_user_task_execution=workflow_execution,
                db_session=self.db_session)

            response_message = workflow_assistant.generate_message()
            response_language = workflow_assistant.language
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
        self.db_session.rollback()
        message = socketio_message_sender.send_error("Error during assistant process_chat_message: " + str(e),
                                                     self.session.session_id,
                                                     user_message_pk=self.session.last_user_message.message_pk)
        self._new_message(message, Message.agent_message_key, 'error')

    def _new_message(self, message, sender, event_name):
        """
        Save message in DB
        :param message: Message to save
        :param sender: Who sent the message
        :return:
        """
        try:
            if sender == Message.user_message_key:
                message_date = message["message_date"]
                timezone_offset = int(message["timezone_offset"])
                message_date = device_date_to_backend_date(message_date, timezone_offset)
            else:
                message_date = datetime.now()
            message = Message(session_id=self.session.session_id, sender=sender, event_name=event_name, message=message,
                              creation_date=datetime.now(), message_date=message_date)
            self.db_session.add(message)
            self.db_session.commit()
            return message
        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"new_message : {e}")
