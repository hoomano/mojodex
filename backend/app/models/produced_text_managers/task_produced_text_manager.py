from models.produced_text_managers.produced_text_manager import ProducedTextManager
from app import db
from models.tasks.tag_manager import TagManager
from mojodex_core.entities.db_base_entities import MdProducedText


class TaskProducedTextManager(ProducedTextManager):
    title_tag_manager = TagManager("title")
    draft_tag_manager = TagManager("draft")

    def __init__(self, session_id, user_id, user_task_execution_pk, task_name_for_system, use_draft_placeholder=False):
        super().__init__(session_id, user_id, use_draft_placeholder, user_task_execution_pk=user_task_execution_pk,
                         task_name_for_system=task_name_for_system)

    @staticmethod
    def get_produced_text_without_tags(text):
        title, production = TaskProducedTextManager.extract_produced_text_from_tagged_text(text)
        return f"{title}\n{production}"

    @staticmethod
    def extract_produced_text_from_tagged_text(mojo_text):
        try:
            # Extract title
            title = TaskProducedTextManager.title_tag_manager.remove_tags_from_text(
                mojo_text) if TaskProducedTextManager.title_tag_manager.start_tag and TaskProducedTextManager.title_tag_manager.end_tag in mojo_text else None
            # Extract production
            if TaskProducedTextManager.draft_tag_manager.start_tag and TaskProducedTextManager.draft_tag_manager.end_tag in mojo_text:
                production = TaskProducedTextManager.draft_tag_manager.remove_tags_from_text(mojo_text)
            else:
                # Backup in case text does not contains correct tags:
                # Remove the one that are presents and returns the whole text without tags
                production = mojo_text.replace(TaskProducedTextManager.self.draft_tag_manager.start_tag, "").replace(
                    TaskProducedTextManager.self.draft_tag_manager.end_tag, "").replace(
                    TaskProducedTextManager.title_tag_manager.start_tag, "").replace(
                    TaskProducedTextManager.title_tag_manager.end_tag, "").strip()
            return title, production
        except Exception as e:
            raise Exception(f"extract_produced_text_from_tagged_text:: {e}")

    def extract_and_save_produced_text_from_tagged_text(self, mojo_text, text_type_pk=None):
        try:
            title, production = self.extract_produced_text_from_tagged_text(mojo_text)
            text_type_pk = text_type_pk if text_type_pk else self._determine_production_text_type_pk(production)
            return self.save_produced_text(production, title, text_type_pk)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: extract_and_save_produced_text:: {e}")

    def _is_edition(self):
        """If is edition, return the produced_text_pk of text to edit, else return None"""
        try:
            # Check if there already is a produced_text for this user_task_execution, if yes, it is an edition
            produced_text = db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.user_task_execution_pk).first()
            return produced_text.produced_text_pk if produced_text else None
        except Exception as e:
            raise Exception(f"_is_edition:: {e}")
