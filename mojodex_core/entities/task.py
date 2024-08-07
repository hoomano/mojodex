from functools import cached_property
from mojodex_core.entities.db_base_entities import MdPlatform, MdPredefinedActionDisplayedData, MdTask, MdTaskDisplayedData, MdTaskPlatformAssociation, MdTaskPredefinedActionAssociation, MdTextEditAction, MdTextEditActionDisplayedData, MdTextEditActionTextTypeAssociation, MdTextType
from sqlalchemy.orm import object_session
from sqlalchemy import case, func, or_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce
from mojodex_core.entities.task_displayed_data import TaskDisplayedData
from mojodex_core.entities.task_predefined_action_association import TaskPredefinedActionAssociation

class Task(MdTask):
    """Task entity class represent an entity containing common informations of an InstructTask or Workflow.
    """

    def _get_displayed_data(self, language_code):
        try:
            session = object_session(self)
            return session.query(MdTaskDisplayedData).filter(MdTaskDisplayedData.task_fk == self.task_pk) \
                .filter(
                or_(
                    MdTaskDisplayedData.language_code == language_code,
                    MdTaskDisplayedData.language_code == 'en'
                )
            ).order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
            ).first()
        except Exception as e:
            raise Exception(f"_get_displayed_data :: {e}")

    def get_name_in_language(self, language_code):
        try:
            return self._get_displayed_data(language_code).name_for_user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_name_in_language :: {e}")

    def get_json_input_in_language(self, language_code):
        try:
            return self._get_displayed_data(language_code).json_input
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_json_input_in_language :: {e}")
        
    def get_predefined_actions_in_language(self, language_code):
        try:
            session = object_session(self)
            predefined_actions_data_en = (session
                .query(
                    MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label("task_predefined_action_association_fk"),
                    MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_en"),
                )
                .filter(MdPredefinedActionDisplayedData.language_code == 'en')
            ).subquery()

            # get predefined actions translated in user's language
            predefined_actions_lang = (session
                .query(
                    MdPredefinedActionDisplayedData.task_predefined_action_association_fk.label("task_predefined_action_association_fk"),
                    MdPredefinedActionDisplayedData.displayed_data.label("displayed_data_lang"),
                )
                .filter(MdPredefinedActionDisplayedData.language_code == language_code)
            ).subquery()

            # get predefined actions translated in user's language or english if not translated
            predefined_actions_data = (session
                .query(
                    MdTaskPredefinedActionAssociation.predefined_action_fk.label("task_fk"),
                    coalesce(
                        predefined_actions_lang.c.displayed_data_lang, 
                        predefined_actions_data_en.c.displayed_data_en
                    ).label("displayed_data"),
                )
                .outerjoin(
                    predefined_actions_lang, 
                    predefined_actions_lang.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                )
                .outerjoin(
                    predefined_actions_data_en,
                    predefined_actions_data_en.c.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                )
                .filter(
                    MdTaskPredefinedActionAssociation.task_fk == self.task_pk
                )
            ).all()
            # predefined_actions_data = (2, {'name': 'Send poem in email', 'button_text': 'Send as email', 'message_prefix': 'Prepare a nice email to send this poem to a friend'})
            # return {"task_pk": 2, 'name': 'Send poem in email', 'button_text': 'Send as email', 'message_prefix': 'Prepare a nice email to send this poem to a friend'}
            return [{"task_pk": task_fk, **displayed_data} for task_fk, displayed_data in predefined_actions_data]
            
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: get_predifined_actions_in_language :: {e}") 
        
    def get_text_edit_actions_in_language(self, language_code):
        """
        Return the text edit actions in the specified language.
        """
        try:
            session = object_session(self)
            
            text_edit_actions_data_en = (session.query(
                MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                MdTextEditActionDisplayedData.name.label("name"),
                MdTextEditActionDisplayedData.description.label("description")
            ).filter(MdTextEditActionDisplayedData.language_code == "en")
            ).subquery()

            text_edit_actions_data_lang = (session.query(
                MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                MdTextEditActionDisplayedData.name.label("name"),
                MdTextEditActionDisplayedData.description.label("description")
            ).filter(MdTextEditActionDisplayedData.language_code == language_code)
            ).subquery()

            text_edit_actions = session.query(
                MdTextEditAction.text_edit_action_pk,
                coalesce(text_edit_actions_data_lang.c.name, text_edit_actions_data_en.c.name).label("name"),
                coalesce(text_edit_actions_data_lang.c.description, text_edit_actions_data_en.c.description).label("description"),
                MdTextEditAction.emoji
            ).outerjoin(
                text_edit_actions_data_lang,
                text_edit_actions_data_lang.c.text_edit_action_fk == MdTextEditAction.text_edit_action_pk
            ).outerjoin(
                text_edit_actions_data_en,
                text_edit_actions_data_en.c.text_edit_action_fk == MdTextEditAction.text_edit_action_pk
            ).join(
                MdTextEditActionTextTypeAssociation,
                MdTextEditActionTextTypeAssociation.text_edit_action_fk == MdTextEditAction.text_edit_action_pk
            ).join(
                MdTextType,
                MdTextType.text_type_pk == MdTextEditActionTextTypeAssociation.text_type_fk
            ).join(
                MdTask,
                MdTask.output_text_type_fk == MdTextType.text_type_pk
            ).filter(MdTask.task_pk == self.task_pk).all()

            return [{"text_edit_action_pk": text_edit_action_pk, "name": name, "description": description, "emoji": emoji} for text_edit_action_pk, name, description, emoji in text_edit_actions]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_text_edit_actions_in_language :: {e}")
        

    @cached_property
    def predefined_actions_association(self) -> list[TaskPredefinedActionAssociation]:
        """
        Returns the predefined actions associated with the task.
        """
        try:
            session = object_session(self)
            return session.query(TaskPredefinedActionAssociation) \
                        .filter(TaskPredefinedActionAssociation.task_fk == self.task_pk) \
                        .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: predefined_actions :: {e}")


    @cached_property
    def platforms(self) -> list[MdPlatform]:
        try:
            session = object_session(self)
            return session.query(MdPlatform) \
                .join(MdTaskPlatformAssociation, MdPlatform.platform_pk == MdTaskPlatformAssociation.platform_fk) \
                .filter(MdTaskPlatformAssociation.task_fk == self.task_pk) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: platforms :: {e}")


    @cached_property
    def output_type(self):
        try:
            session = object_session(self)
            return session.query(MdTextType).get(self.output_text_type_fk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_type :: {e}")
        

    @cached_property
    def display_data(self) -> list[TaskDisplayedData]:
        try:
            session = object_session(self)
            return session.query(TaskDisplayedData).filter(TaskDisplayedData.task_fk == self.task_pk).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: displayed_data :: {e}")
        

    def to_json(self):
        try:
            return {
                "task_type": self.type,
                "platforms": [platform.name for platform in self.platforms],
                "predefined_actions":  [predefined_action.to_json() for predefined_action in self.predefined_actions_association],
                "task_displayed_data": [display_data.to_json() for display_data in self.display_data],
                "name_for_system": self.name_for_system,
                "definition_for_system": self.definition_for_system,
                "output_type": self.output_type.name,
                "icon": self.icon,
                "result_chat_enabled": self.result_chat_enabled
                }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")