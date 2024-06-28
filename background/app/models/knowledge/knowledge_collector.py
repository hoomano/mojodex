from datetime import datetime, timedelta, timezone

from mojodex_core.logging_handler import MojodexCoreLogger

from mojodex_core.llm_engine.mpt import MPT

class KnowledgeCollector:

    def __init__(self, user_name, user_timezone_offset, user_summary, user_company_knowledge, user_business_goal):
        self.mojo_knowledge = self.get_mojo_knowledge()
        self.global_context = self.get_global_context_knowledge(user_timezone_offset if user_timezone_offset else 0)
        self.user_timezone_offset = user_timezone_offset
        self.user_name = user_name
        self.user_summary = user_summary
        self.user_company_knowledge = user_company_knowledge
        self.user_business_goal= user_business_goal

        self.logger = MojodexCoreLogger("KnowledgeCollector")

    @staticmethod
    def get_mojo_knowledge():
        with open("mojodex_core/prompts/knowledge/mojo_knowledge.txt", 'r') as f:
            return f.read()

    @staticmethod
    def get_global_context_knowledge(timezone_offset=0):
        """Returns the global context knowledge for the current time
        :param timezone_offset: offset in minutes to remove from UTC time to get user time"""
        timestamp = datetime.now(timezone.utc)
        timestamp -= timedelta(minutes=timezone_offset)
        global_context = MPT("mojodex_core/instructions/global_context.mpt",
                             weekday=timestamp.strftime("%A"),
                                   datetime=timestamp.strftime("%d %B %Y"),
                                   time=timestamp.strftime("%H:%M"))
        return global_context.prompt
    
    @property
    def mojodex_knowledge(self):
        return MPT("mojodex_core/instructions/mojodex_knowledge.mpt")
    
    @property
    def localized_context(self):
        try:
            timestamp = datetime.now(timezone.utc)
            if self.user_timezone_offset:
                timestamp -= timedelta(minutes=self.user_timezone_offset)
            return MPT("mojodex_core/instructions/global_context.mpt",
                                weekday=timestamp.strftime("%A"),
                                    datetime=timestamp.strftime("%d %B %Y"),
                                    time=timestamp.strftime("%H:%M"))
        except Exception as e:
            self.logger.error(f"Error getting localized context: {e}")
            return KnowledgeCollector.get_global_context_knowledge(self.user_timezone_offset)


