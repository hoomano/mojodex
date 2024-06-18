from app import db
from background_logger import BackgroundLogger
from mojodex_core.entities.db_base_entities import MdSession


class LanguageRetriever:
    logger_prefix = "LanguageRetriever::"

    def __init__(self):
        self.logger = BackgroundLogger(LanguageRetriever.logger_prefix)

    def get_language_from_session_or_user(self, session_id, user):
        try:
            self.logger.debug(f"_get_session_language")
            session_language = \
            db.session.query(MdSession.language).filter(MdSession.session_id == session_id).first()[0]
            return session_language if session_language else user.language_code
        except Exception as e:
            raise Exception(f"{self.logger_prefix} _get_session_language:: {e}")