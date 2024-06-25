from abc import ABC, abstractmethod
from datetime import datetime
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdProducedText, MdProducedTextVersion, MdTextType
from mojodex_core.db import with_db_session
from mojodex_core.llm_engine.providers.model_loader import ModelLoader
from mojodex_core.llm_engine.mpt import MPT


class ProducedTextManager(ABC):
    get_text_type_mpt_filename = "instructions/get_text_type.mpt"

    def __init__(self, session_id, user_id=None, use_draft_placeholder=False, user_task_execution_pk=None,
                 task_name_for_system=None):
        self.session_id = session_id
        self.user_id = user_id
        self.use_draft_placeholder = use_draft_placeholder
        self.user_task_execution_pk, self.task_name_for_system = user_task_execution_pk, task_name_for_system

    @with_db_session
    def save_produced_text(self, text, title, text_type_pk, db_session):
        try:
            text_to_edit_pk = self._is_edition()
            if text_to_edit_pk is not None:
                produced_text = db_session.query(MdProducedText).filter(
                    MdProducedText.produced_text_pk == text_to_edit_pk).first()
            else:
                produced_text = MdProducedText(user_task_execution_fk=self.user_task_execution_pk,
                                               user_id=self.user_id, session_id=self.session_id)
                db_session.add(produced_text)
                db_session.flush()
                db_session.refresh(produced_text)

            try:
                embedding = ProducedTextManager.embed_produced_text(title, text, self.user_id,
                                                                    user_task_execution_pk=self.user_task_execution_pk,
                                                                    task_name_for_system=self.task_name_for_system)
            except Exception as e:
                log_error(f"{self.__class__.__name__} : save_produced_text:: error embedding text: {e}")
                embedding = None

            text_type_pk = text_type_pk if text_type_pk else self._determine_production_text_type_pk(text, db_session)
            new_version = MdProducedTextVersion(produced_text_fk=produced_text.produced_text_pk, title=title,
                                                production=text,
                                                creation_date=datetime.now(), text_type_fk=text_type_pk,
                                                embedding=embedding)
            db_session.add(new_version)
            db_session.commit()
            return produced_text, new_version
        except Exception as e:
            raise Exception(f"save_produced_text:: {e}")

    @abstractmethod
    def _is_edition(self, *args, **kwargs):
        """Determines if current produced text is an edition of a previous one.
        If it is, returns the produced_text_pk of the text to edit, else returns None"""
        raise NotImplementedError

    def _determine_production_text_type_pk(self, production, db_session):
        """Return the type of the produced text among the available enum, based on the text itself, determined by the MPT get_text_type.mpt"""
        try:
            types_enum = db_session.query(MdTextType).all()

            get_text_type_mpt = MPT(
                ProducedTextManager.get_text_type_mpt_filename, text=production, types_enum=types_enum)

            responses = get_text_type_mpt.run(user_id=self.user_id,
                                              temperature=0, max_tokens=20,
                                              user_task_execution_pk=self.user_task_execution_pk,
                                              task_name_for_system=self.task_name_for_system,
                                              )
            text_type = responses[0].strip().lower()
            if text_type not in types_enum:
                return None
            return db_session.query(MdTextType.text_type_pk).filter(
                MdTextType.name == text_type).first()[0]
        except Exception as e:
            raise Exception(f"_determine_produced_text_type:: {e}")

    @staticmethod
    def embed_produced_text(title, production, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            text_to_embedded = f"{title}\n\n{production}"
            embedded_text = ModelLoader().embedding_provider.embed(text_to_embedded, user_id,
                                                                   label="PRODUCED_TEXT_EMBEDDER",
                                                                   user_task_execution_pk=user_task_execution_pk,
                                                                   task_name_for_system=task_name_for_system)
            return embedded_text
        except Exception as e:
            raise Exception(f"embed_produced_text :: {e}")
