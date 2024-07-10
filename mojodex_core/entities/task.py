import json
from mojodex_core.entities.db_base_entities import MdPredefinedActionDisplayedData, MdTask, MdTaskDisplayedData, MdTaskPredefinedActionAssociation, MdTextEditAction, MdTextEditActionDisplayedData, MdTextEditActionTextTypeAssociation, MdTextType
from sqlalchemy.orm import object_session
from sqlalchemy import case, func, or_
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import aliased

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
            # get predefined actions translated in english
            predefined_actions_data = (
                session
                .query(
                    MdTaskPredefinedActionAssociation.predefined_action_fk.label("task_fk"),
                    coalesce(
                        case(
                            (MdPredefinedActionDisplayedData.language_code == language_code, MdPredefinedActionDisplayedData.displayed_data),
                            else_=None),
                        case(
                            (MdPredefinedActionDisplayedData.language_code == 'en', MdPredefinedActionDisplayedData.displayed_data),
                            else_=None)
                    ).label("displayed_data")
                )
                .outerjoin(
                    MdPredefinedActionDisplayedData,
                    MdTaskPredefinedActionAssociation.task_predefined_action_association_pk == MdPredefinedActionDisplayedData.task_predefined_action_association_fk
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
            MdTextEditActionSpecifiedLang = aliased(MdTextEditActionDisplayedData)
            MdTextEditActionEnglishLang = aliased(MdTextEditActionDisplayedData)

            text_edit_actions = (session.query(
                    MdTextEditAction.text_edit_action_pk,
                    func.coalesce(MdTextEditActionSpecifiedLang.name, MdTextEditActionEnglishLang.name).label("name"),
                    func.coalesce(MdTextEditActionSpecifiedLang.description, MdTextEditActionEnglishLang.description).label("description"),
                    MdTextEditAction.emoji,)
                .outerjoin(
                    MdTextEditActionSpecifiedLang,
                    (MdTextEditAction.text_edit_action_pk == MdTextEditActionSpecifiedLang.text_edit_action_fk) &
                    (MdTextEditActionSpecifiedLang.language_code == language_code))
                .outerjoin(
                    MdTextEditActionEnglishLang,
                    (MdTextEditAction.text_edit_action_pk == MdTextEditActionEnglishLang.text_edit_action_fk) &
                    (MdTextEditActionEnglishLang.language_code == "en"))
                .join(
                    MdTextEditActionTextTypeAssociation,
                    MdTextEditActionTextTypeAssociation.text_edit_action_fk == MdTextEditAction.text_edit_action_pk,)
                .join(
                    MdTextType,
                    MdTextType.text_type_pk == MdTextEditActionTextTypeAssociation.text_type_fk,)
                .join(
                    MdTask,
                    MdTask.output_text_type_fk == MdTextType.text_type_pk,)
                .filter(MdTask.task_pk == self.task_pk)
                ).all()
            return [{"text_edit_action_pk": text_edit_action_pk, "name": name, "description": description, "emoji": emoji} for text_edit_action_pk, name, description, emoji in text_edit_actions]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_text_edit_actions_in_language :: {e}")
        

    @property
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
            