from mojodex_core.entities_controllers.entity_controller import EntityController
from mojodex_core.entities import MdUserTaskExecution, MdProducedText, MdTask
from mojodex_core.db import Session as DbSession
from mojodex_core.entities_controllers.user_task import UserTask
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.entities_controllers.task import Task
from mojodex_core.entities_controllers.user import User
from mojodex_core.entities_controllers.session import Session
from mojodex_core.entities_controllers.workflow import Workflow
from mojodex_core.entities_controllers.instruct_task import InstructTask
from mojodex_core.knowledge_manager import knowledge_manager

class UserTaskExecution(EntityController):
    def __init__(self, user_task_execution_pk: int, db_session: DbSession, task: Task = None, user: User = None, session: Session = None):
        super().__init__(MdUserTaskExecution, user_task_execution_pk, db_session)
        self.task = task if task else self._create_task_controller()
        self.user = user if user else User(self.db_object.user_id, self.db_session)
        self.session = session if session else Session(self.db_object.session_id, self.db_session)


    def _create_task_controller(self):
        try:
            task_type = self.db_session.query(MdTask.type).filter(MdTask.task_pk == self.user_task.task_fk).first()[0]
            if task_type == "instruct":
                return InstructTask(self.user_task.task_fk, self.db_session)
            elif task_type == "workflow":
                return Workflow(self.user_task.task_fk, self.db_session)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _create_task_controller :: {e}")

    @property
    def user_task(self):
        try:
             return UserTask(self.db_object.user_task_fk, self.db_session)
        except Exception as e:
            raise Exception(f"_get_user_task :: {e}")

    @property
    def user_task_execution_pk(self):
        return self.pk

    @property
    def user_task_inputs(self):
        try:
            return self.db_object.json_input_values
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_task_inputs :: {e}")

    @property
    def has_images_inputs(self):
        try:
            for input in self.user_task_inputs:
                if input["type"] in ["image", "multiple_images"]:
                    return True
            return False
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: has_images_inputs :: {e}")

    @property
    def images_input_names(self):
        try:
            input_images = []
            for task_input in self.user_task_inputs:
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
            raise Exception(f"{self.__class__.__name__} :: task_name_in_user_language :: {e}")

    @property
    def produced_text_done(self):
        try:
            return self.db_session.query(MdProducedText).filter(MdProducedText.user_task_execution_fk == self.pk).count() > 1
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}")

    @property
    def title(self):
        try:
            return self.db_object.title
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: title :: {e}")

    @title.setter
    def title(self, title):
        try:
            self.db_object.title = title
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: title :: {e}")

    @property
    def summary(self):
        try:
            return self.db_object.summary
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: summary :: {e}")

    @summary.setter
    def summary(self, summary):
        try:
            self.db_object.summary = summary
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: summary :: {e}")

    def generate_title_and_summary(self):
        try:
            task_execution_summary = MPT("instructions/task_execution_summary.mpt",
                                         mojo_knowledge=knowledge_manager.mojodex_knowledge,
                                         global_context=knowledge_manager.global_context_knowledge,
                                         username=self.user.username,
                                         user_company_knowledge=self.user.company_knowledge,
                                         task=self.task,
                                         user_task_inputs=self.user_task_inputs,
                                         user_messages_conversation=self.session.get_conversation_as_string())

            responses = task_execution_summary.run(user_id=self.user.user_id,
                                                   temperature=0, max_tokens=500,
                                                   user_task_execution_pk=self.pk,
                                                   task_name_for_system=self.task.name_for_system,
                                                   )
            response = responses[0]
            self.title = response.split("<title>")[1].split("</title>")[0]
            self.summary = response.split("<summary>")[1].split("</summary>")[0]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: generate_title_and_summary :: {e}")
