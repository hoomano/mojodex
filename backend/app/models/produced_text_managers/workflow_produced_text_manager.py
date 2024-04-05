from models.produced_text_managers.produced_text_manager import ProducedTextManager
from mojodex_backend_logger import MojodexBackendLogger


class WorkflowProducedTextManager(ProducedTextManager):
    logger_prefix = "📝 WorkflowProducedTextManager"
    generate_workflow_produced_text_title = "instructions/generate_workflow_produced_text_title.mpt"

    def __init__(self, session_id, user_id, user_workflow_execution_pk, use_draft_placeholder=False):
        self.logger = MojodexBackendLogger(ProducedTextManager.logger_prefix)
        super().__init__(session_id, user_id, use_draft_placeholder,
                         user_task_execution_pk=user_workflow_execution_pk, logger=self.logger)

    def _is_edition(self):
        """If is edition, return the produced_text_pk of text to edit, else return None"""
        # For now, a workflow can only have one produced text so no edition
        return None

    def save(self, production, text_type_pk):
        try:
            self.logger.debug(f"extract_and_save_produced_text")
            title = "" # For now, we are not sure a workflow produced text needs a title so we leave it blank so that user can edit it
            text_type_pk = text_type_pk if text_type_pk else self._determine_production_text_type_pk(production)
            return self._save_produced_text(production, title, text_type_pk)
        except Exception as e:
            raise Exception(
                f"{ProducedTextManager.logger_prefix}:: generate_title_and_save:: {e}")
