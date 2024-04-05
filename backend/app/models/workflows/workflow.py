from sqlalchemy import or_, func
from mojodex_core.entities import MdTask, MdTaskDisplayedData, MdUserTask, MdUser, MdWorkflowStep, MdWorkflowStepDisplayedData
from sqlalchemy.sql.functions import coalesce


class Workflow:
    def __init__(self, db_object, db_session, user_id):
        self.db_object = db_object
        self.db_session = db_session
        self.user_id = user_id

    @property
    def name_for_system(self):
        return self.db_object.name_for_system

    @property
    def definition_for_system(self):
        return self.db_object.definition_for_system

    @property
    def _db_displayed_data(self):
        return self.db_session.query(MdTaskDisplayedData) \
            .join(MdTask, MdTask.task_pk == MdTaskDisplayedData.task_fk) \
            .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
            .join(MdUser, MdUser.user_id == self.user_id) \
            .filter(MdTaskDisplayedData.task_fk == self.db_object.task_pk) \
            .filter(
            or_(MdTaskDisplayedData.language_code == MdUser.language_code,
                MdTaskDisplayedData.language_code == 'en')) \
            .order_by(
            # Sort by user's language first otherwise by english
            func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
        ).first()

    @property
    def name_for_user(self):
        return self._db_displayed_data.name_for_user

    @property
    def definition_for_user(self):
        return self._db_displayed_data.definition_for_user

    @property
    def db_steps(self):
        return self.db_session.query(MdWorkflowStep) \
            .filter(MdWorkflowStep.task_fk == self.db_object.task_pk) \
            .order_by(MdWorkflowStep.rank.asc()).all()


    @property
    def db_steps_with_translation(self):
        user_lang_subquery = (
            self.db_session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("user_lang_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
            )
            .join(MdUser, MdUser.user_id == self.user_id)
            .filter(MdWorkflowStepDisplayedData.language_code == MdUser.language_code)
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
            .filter(MdWorkflowStep.workflow_fk == self.db_object.workflow_pk) \
            .order_by(MdWorkflowStep.rank) \
            .all()

        return steps

    @property
    def json_steps(self):
        return [{
            'workflow_step_pk': db_step.workflow_step_pk,
            'step_name_for_user': name_for_user,
            'step_definition_for_user': definition_for_user
        } for db_step, name_for_user, definition_for_user in self.db_steps_with_translation
        ]
