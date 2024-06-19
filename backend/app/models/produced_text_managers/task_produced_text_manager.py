from models.produced_text_managers.produced_text_manager import ProducedTextManager
from mojodex_backend_logger import MojodexBackendLogger
from app import db
from mojodex_core.entities.db_base_entities import MdProducedText

class TaskProducedTextManager(ProducedTextManager):
    logger_prefix = "📝 TaskProducedTextManager"
    
    title_start_tag, title_end_tag = "<title>", "</title>"
    draft_start_tag, draft_end_tag = "<draft>", "</draft>"

    def __init__(self, session_id, user_id, user_task_execution_pk, task_name_for_system, use_draft_placeholder=False):
        self.logger = MojodexBackendLogger(
            f"{ProducedTextManager.logger_prefix} user_task_execution_pk {user_task_execution_pk}")
        super().__init__(session_id, user_id, use_draft_placeholder, user_task_execution_pk=user_task_execution_pk,
                         task_name_for_system=task_name_for_system, logger=self.logger)


    @staticmethod
    def remove_tags(text):
        return text.replace(TaskProducedTextManager.draft_start_tag, "").replace(TaskProducedTextManager.draft_end_tag, "") \
            .replace(TaskProducedTextManager.title_start_tag, "").replace(TaskProducedTextManager.title_end_tag, "")


    def _extract_produced_text_title_from_tagged_text(self, mojo_text):
        try:
            if self.title_start_tag and self.title_end_tag in mojo_text:
                start = mojo_text.find(self.title_start_tag) + len(self.title_start_tag)
                end = mojo_text.find(self.title_end_tag)
                return mojo_text[start:end].strip()
            return None
        except Exception as e:
            raise Exception(
                f"_extract_produced_text_title_from_tagged_text:: {e}")

    def _extract_produced_text_production_from_tagged_text(self, mojo_text):
        try:
            if self.draft_start_tag and self.draft_end_tag in mojo_text:
                start = mojo_text.find(
                    self.draft_start_tag) + len(self.draft_start_tag)
                end = mojo_text.find(self.draft_end_tag)
                return mojo_text[start:end].strip()
            return mojo_text.replace(self.draft_start_tag, "").replace(
                self.draft_end_tag, "").replace(self.title_start_tag, "").replace(
                self.title_end_tag, "").strip()
        except Exception as e:
            raise Exception(
                f"_extract_produced_text_production_from_tagged_text:: {e}")

    def _extract_produced_text_from_tagged_text(self, mojo_text):
        try:
            # Extract title
            title = self._extract_produced_text_title_from_tagged_text(mojo_text)

            # Extract production
            production = self._extract_produced_text_production_from_tagged_text(mojo_text)
            return title, production
        except Exception as e:
            raise Exception(
                f"_extract_produced_text_from_tagged_text:: {e}")

    def extract_and_save_produced_text_from_tagged_text(self, mojo_text, text_type_pk=None):
        try:
            self.logger.debug(f"extract_and_save_produced_text")
            title, production = self._extract_produced_text_from_tagged_text(mojo_text)
            text_type_pk = text_type_pk if text_type_pk else self._determine_production_text_type_pk(production)
            return self.save_produced_text(production, title, text_type_pk)
        except Exception as e:
            raise Exception(
                f"{ProducedTextManager.logger_prefix}:: extract_and_save_produced_text:: {e}")

    def _is_edition(self):
        """If is edition, return the produced_text_pk of text to edit, else return None"""
        try:
            # Check if there already is a produced_text for this user_task_execution, if yes, it is an edition
            produced_text = db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.user_task_execution_pk).first()
            return produced_text.produced_text_pk if produced_text else None
        except Exception as e:
            raise Exception(f"_is_edition:: {e}")