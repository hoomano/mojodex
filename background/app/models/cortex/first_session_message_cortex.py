from mojodex_core.entities.db_base_entities import *
from background_logger import BackgroundLogger
from models.session_title_generator import SessionTitleGenerator
from app import db, language_retriever

from models.knowledge.knowledge_collector import KnowledgeCollector


class FirstSessionMessageCortex:
    logger_prefix = "FirstSessionMessageCortex::"

    def __init__(self, sender, message, session_id):
        try:
            self.logger = BackgroundLogger(f"{FirstSessionMessageCortex.logger_prefix}")
            self.sender = sender
            self.message = message
            self.session_id = session_id
            self.session_date = self.__get_session_date()
            self.user, self.company = self.__get_user_and_company()
            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user.summary, self.user.company_description, self.user.goal)
            self.language = language_retriever.get_language_from_session_or_user(self.session_id, self.user)
            self.logger.debug("__init__")
        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def generate_session_title(self):
        try:
            session_title_generator = SessionTitleGenerator(self.session_id, self.user.user_id, self.knowledge_collector)
            session_title_generator.generate_session_title(self.sender, self.message, self.session_date, self.language)
        except Exception as e:
            self.logger.error(f"generate_session_title :: {e}")

    def __get_session_date(self):
        try:
            return db.session.query(MdSession.creation_date).filter(MdSession.session_id == self.session_id).first()[0]
        except Exception as e:
            self.logger.error(f"__get_session_date :: {e}")
            
            
    def __get_user_and_company(self):
        try:
            return db.session.query(MdUser, MdCompany)\
                .join(MdSession, MdSession.user_id == MdUser.user_id)\
                .join(MdCompany, MdUser.company_fk == MdCompany.company_pk)\
                .filter(MdSession.session_id == self.session_id).first()
        except Exception as e:
            self.logger.error(f"__get_user_and_company :: {e}")

