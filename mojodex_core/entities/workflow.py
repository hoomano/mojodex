
from mojodex_core.entities.db_base_entities import MdWorkflowStepDisplayedData, MdWorkflowStep
from mojodex_core.entities.task import Task
from sqlalchemy.orm import object_session
from sqlalchemy.sql.functions import coalesce


from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.steps_library import steps_class


class Workflow(Task):


    @property
    def steps(self):
        try:
            session = object_session(self)
            steps = []
            md_steps = session.query(MdWorkflowStep) \
                .filter(MdWorkflowStep.task_fk == self.task_pk) \
                .order_by(MdWorkflowStep.rank.asc()).all()
            for md_step in md_steps:
                step_class = steps_class[md_step.name_for_system] if md_step.name_for_system in steps_class else WorkflowStep
                step = session.query(step_class).get(md_step.workflow_step_pk)
                steps.append(step)
            return steps

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: steps :: {e}")

    def _get_db_steps_with_translation(self, language_code):
        session = object_session(self)
        user_lang_subquery = (
            session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("user_lang_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("user_lang_definition_for_user"),
            )
            .filter(MdWorkflowStepDisplayedData.language_code == language_code)
            .subquery()
        )

        # Subquery for 'en'
        en_subquery = (
            session.query(
                MdWorkflowStepDisplayedData.workflow_step_fk.label("workflow_step_fk"),
                MdWorkflowStepDisplayedData.name_for_user.label("en_name_for_user"),
                MdWorkflowStepDisplayedData.definition_for_user.label("en_definition_for_user"),
            )
            .filter(MdWorkflowStepDisplayedData.language_code == "en")
            .subquery()
        )

        md_steps = session.query(MdWorkflowStep, coalesce(
            user_lang_subquery.c.user_lang_name_for_user,
            en_subquery.c.en_name_for_user).label(
            "name_for_user"),
                                 coalesce(
                                     user_lang_subquery.c.user_lang_definition_for_user,
                                     en_subquery.c.en_definition_for_user).label(
                                     "definition_for_user")) \
            .outerjoin(user_lang_subquery, MdWorkflowStep.workflow_step_pk == user_lang_subquery.c.workflow_step_fk) \
            .outerjoin(en_subquery, MdWorkflowStep.workflow_step_pk == en_subquery.c.workflow_step_fk) \
            .filter(MdWorkflowStep.task_fk == self.task_pk) \
            .order_by(MdWorkflowStep.rank) \
            .all()
        steps = []
        for db_step, name_for_user, definition_for_user in md_steps:
            step_name_for_system = db_step.name_for_system
            step_class = steps_class[step_name_for_system] if step_name_for_system in steps_class else WorkflowStep
            step = session.query(step_class).get(db_step.workflow_step_pk)
            steps.append((step, name_for_user, definition_for_user))

        return steps

    def get_json_steps_with_translation(self, language_code):
        return [{
            'workflow_step_pk': db_step.workflow_step_pk,
            'step_name_for_user': name_for_user,
            'step_definition_for_user': definition_for_user
        } for db_step, name_for_user, definition_for_user in self._get_db_steps_with_translation(language_code)
        ]
