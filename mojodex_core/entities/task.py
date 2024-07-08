import json
from mojodex_core.entities.db_base_entities import MdPredefinedActionDisplayedData, MdTask, MdTaskDisplayedData, MdTaskPredefinedActionAssociation
from sqlalchemy.orm import object_session
from sqlalchemy import case, func, or_
from sqlalchemy.sql.functions import coalesce

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