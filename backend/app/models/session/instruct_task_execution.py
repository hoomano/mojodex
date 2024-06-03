from jinja2 import Template

from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from mojodex_core.db import engine, Session
from mojodex_core.entities import MdTask, MdUser, MdUserTaskExecution, MdUserTask, MdMessage, MdTaskDisplayedData
from sqlalchemy import func, or_

class InstructTask:

    def __init__(self, task_pk, db_session):
        self.task_pk = task_pk
        self.db_session = db_session
        self.db_object = self._get_db_object(task_pk)


    def _get_db_object(self, task_pk):
        try:
            return self.db_session.query(MdTask).filter(MdTask.task_pk == task_pk).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    @property
    def infos_to_extract(self):
        try:
            return self.db_object.infos_to_extract
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: infos_to_extract :: {e}")

    @property
    def name_for_system(self):
        try:
            return self.db_object.name_for_system
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: name_for_system :: {e}")

    @property
    def description(self):
        try:
            return self.db_object.definition_for_system
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: description :: {e}")

    @property
    def icon(self):
        try:
            return self.db_object.icon
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: icon :: {e}")


    @property
    def output_format_instruction_title(self):
        try:
            return self.db_object.output_format_instruction_title
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_title :: {e}")

    @property
    def output_format_instruction_draft(self):
        try:
            return self.db_object.output_format_instruction_draft
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_draft :: {e}")

    @property
    def final_instruction(self):
        try:
            return self.db_object.final_instruction
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: final_instruction :: {e}")

    @property
    def output_text_type_fk(self):
        try:
            return self.db_object.output_text_type_fk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_text_type_fk :: {e}")


    def get_name_in_language(self, language_code):
        try:
            return self.db_session.query(MdTaskDisplayedData.name_for_user).filter(MdTaskDisplayedData.task_fk == self.task_pk) \
                .filter(
                or_(
                    MdTaskDisplayedData.language_code == language_code,
                    MdTaskDisplayedData.language_code == 'en'
                )
            ).order_by(
                        # Sort by user's language first otherwise by english
                        func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
                    ).first()[0]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_name_in_language :: {e}")

class User:

    def __init__(self, user_id, db_session):
        self.user_id = user_id
        self.db_session = db_session
        self.db_object = self._get_db_object(user_id)


    def _get_db_object(self, user_id):
        try:
            return self.db_session.query(MdUser).filter(MdUser.user_id == user_id).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    @property
    def company_knowledge(self):
        try:
            return self.db_object.company_description
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: company_knowledge :: {e}")

    @property
    def username(self):
        try:
            return self.db_object.name
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: username :: {e}")

    @property
    def language_code(self):
        try:
            return self.db_object.language_code
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: language_code :: {e}")


class ChatSession:
    def __init__(self, session_id, db_session):
        self.session_id = session_id
        self.db_session = db_session

    @property
    def _db_messages(self):
        try:
            return self.db_session.query(MdMessage).filter(MdMessage.session_id == self.session_id).order_by(
                MdMessage.message_date).all()
        except Exception as e:
            raise Exception("_db_messages: " + str(e))

    @property
    def conversation(self):
        try:
            user_key = "user"
            agent_key = "assistant"
            messages = self._db_messages
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                elif message.sender == "system":
                    conversation.append({"role": "system", "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: messages: " + str(e))

class InstructTaskExecution:
    task_specific_instructions_prompt = "mojodex_core/prompts/tasks/task_specific_instructions.txt"

    def __del__(self):
        self.db_session.close()

    def __init__(self, user_task_execution_pk):
        try:
            self.db_session = Session(engine)
            self.user_task_execution_pk = user_task_execution_pk
            self.db_object = self._get_db_object(user_task_execution_pk)
            user_task = self._get_user_task()
            self.user = User(user_task.user_id, self.db_session)
            self.task = InstructTask(user_task.task_fk, self.db_session)
            self.session = ChatSession(self.db_object.session_id, self.db_session)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def _get_db_object(self, user_task_execution_pk):
        try:
            return self.db_session.query(MdUserTaskExecution).filter(
                MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    def _get_user_task(self):
        try:
            return self.db_session.query(MdUserTask).filter(
                MdUserTask.user_task_pk == self.db_object.user_task_fk).first()
        except Exception as e:
            raise Exception(f"_get_user_task :: {e}")



    @property
    def produced_text_done(self):
        try:
            pass
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}")

    @property
    def user_task_inputs(self):
        try:
            return self.db_object.json_input_values
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_inputs :: {e}")

    @property
    def instructions(self):
        try:
            with open(self.task_specific_instructions_prompt, 'r') as f:
                template = Template(f.read())
            return template.render(task=self.task,
                                   user_task_inputs=self.user_task_inputs,
                                   title_start_tag=InstructTaskProducedTextManager.title_start_tag,
                                   title_end_tag=InstructTaskProducedTextManager.title_end_tag,
                                   draft_start_tag=InstructTaskProducedTextManager.draft_start_tag,
                                   draft_end_tag=InstructTaskProducedTextManager.draft_end_tag,
                                   #task_tool_associationstask_tool_associations
                                   )
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: instructions :: {e}")

    @property
    def has_images_inputs(self):
        try:
            for input in self.user_task_inputs:
                if input["type"] == "image":
                    return True
            return False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: has_images_inputs :: {e}")

    @property
    def images_input_names(self):
        try:
            input_images = [input["value"] for input in self.user_task_inputs if input["type"] == "image"]
            return input_images
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: images_input_names :: {e}")
