from mojodex_core.entities.db_base_entities import MdWorkflowStep, MdWorkflowStepDisplayedData
from sqlalchemy.sql.functions import coalesce


class Workflow:
    def __init__(self, db_object, db_session):
        self.db_object = db_object
        self.db_session = db_session

    @property
    def name_for_system(self):
        return self.db_object.name_for_system

    @property
    def definition_for_system(self):
        return self.db_object.definition_for_system


    @property
    def db_steps(self):
        return self.db_session.query(MdWorkflowStep) \
            .filter(MdWorkflowStep.task_fk == self.db_object.task_pk) \
            .order_by(MdWorkflowStep.rank.asc()).all()

    def _get_db_steps_with_translation(self, language_code):
        user_lang_subquery = (
            self.db_session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("user_lang_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
            )
            .filter(MdWorkflowStepDisplayedData.language_code == language_code)
            .subquery()
        )

        # Subquery for 'en'
        en_subquery = (
            self.db_session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("en_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("en_definition_for_user"),
            )
            .filter(MdWorkflowStepDisplayedData.language_code == "en")
            .subquery()
        )

        steps = self.db_session.query(MdWorkflowStep, coalesce(
            user_lang_subquery.c.user_lang_name_for_user,
            en_subquery.c.en_name_for_user).label(
            "name_for_user"),
                                 coalesce(
                                     user_lang_subquery.c.user_lang_definition_for_user,
                                     en_subquery.c.en_definition_for_user).label(
                                     "definition_for_user")) \
            .outerjoin(user_lang_subquery, MdWorkflowStep.workflow_step_pk == user_lang_subquery.c.workflow_step_fk) \
            .outerjoin(en_subquery, MdWorkflowStep.workflow_step_pk == en_subquery.c.workflow_step_fk) \
            .filter(MdWorkflowStep.task_fk == self.db_object.task_pk) \
            .order_by(MdWorkflowStep.rank) \
            .all()

        return steps

    def get_json_steps_with_translation(self, language_code):
        return [{
            'workflow_step_pk': db_step.workflow_step_pk,
            'step_name_for_user': name_for_user,
            'step_definition_for_user': definition_for_user
        } for db_step, name_for_user, definition_for_user in self._get_db_steps_with_translation(language_code)
        ]
