from abc import ABC, abstractmethod

from mojodex_core.entities.abstract_entity import AbstractEntity
from mojodex_core.entities.db_base_entities import MdUserTaskExecution, MdProducedText
from sqlalchemy.orm import object_session

from mojodex_core.entities.session import Session
from mojodex_core.knowledge_manager import knowledge_manager

from mojodex_core.entities.user_task import UserTask
from mojodex_core.llm_engine.mpt import MPT


class UserTaskExecution(MdUserTaskExecution, ABC, metaclass=AbstractEntity):

    @property
    def produced_text_done(self):
        try:
            session = object_session(self)
            return session.query(MdProducedText).filter(MdProducedText.user_task_execution_fk == self.user_task_execution_pk).count() > 1
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: produced_text_done :: {e}")

    @property
    def has_images_inputs(self):
        try:
            for input in self.json_input_values:
                if input["type"] in ["image", "multiple_images"]:
                    return True
            return False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: has_images_inputs :: {e}")

    @property
    def images_input_names(self):
        try:
            input_images = []
            for task_input in self.json_input_values:
                if task_input["type"] == "image":
                    input_images.append(task_input["value"])
                elif task_input["type"] == "multiple_images":
                    input_images += task_input["value"]
            return input_images
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: images_input_names :: {e}")

    @property
    def task_name_in_user_language(self):
        try:
            return self.task.get_name_in_language(self.user.language_code)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_task_name_in_user_language :: {e}")

    @property
    @abstractmethod
    def user_task(self):
        try:
            session = object_session(self)
            return session.query(UserTask).filter(UserTask.user_task_pk == self.user_task_fk).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task :: {e}")

    @property
    def user(self):
        try:
            return self.user_task.user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user :: {e}")

    @property
    def task(self):
        try:
            return self.user_task.task
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: task :: {e}")

    @property
    def session(self):
        try:
            session = object_session(self)
            return session.query(Session).filter(Session.session_id == self.session_id).first()
        except Exception as e:
            raise Exception(f"{self.__class__} :: session :: {e}")

    def generate_title_and_summary(self):
        try:
            session = object_session(self)
            print(f"👉 generate_title_and_summary : {session}")
            task_execution_summary = MPT("instructions/task_execution_summary.mpt",
                                         mojo_knowledge=knowledge_manager.mojodex_knowledge,
                                         global_context=knowledge_manager.global_context_knowledge,
                                         username=self.user.name,
                                         user_company_knowledge=self.user.company_description,
                                         task=self.task,
                                         user_task_inputs=self.json_input_values,
                                         user_messages_conversation=self.session.get_conversation_as_string())

            responses = task_execution_summary.run(user_id=self.user.user_id,
                                                   temperature=0, max_tokens=500,
                                                   user_task_execution_pk=self.user_task_execution_pk,
                                                   task_name_for_system=self.task.name_for_system,
                                                   )
            response = responses[0]
            self.title = response.split("<title>")[1].split("</title>")[0]
            self.summary = response.split("<summary>")[1].split("</summary>")[0]
            session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: generate_title_and_summary :: {e}")
