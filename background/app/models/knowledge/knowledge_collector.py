from datetime import datetime, timedelta
from jinja2 import Template

class KnowledgeCollector:

    def __init__(self, user_name, user_timezone_offset, user_summary, user_company_knowledge, user_business_goal):
        self.mojo_knowledge = self.get_mojo_knowledge()
        self.global_context = self.get_global_context_knowledge(user_timezone_offset)
        self.user_name = user_name
        self.user_summary = user_summary
        self.user_company_knowledge = user_company_knowledge
        self.user_business_goal= user_business_goal

    @staticmethod
    def get_mojo_knowledge():
        with open("/data/knowledge/mojo_knowledge.txt", 'r') as f:
            return f.read()

    @staticmethod
    def get_global_context_knowledge(timezone_offset=0):
        """Returns the global context knowledge for the current time
        :param timezone_offset: offset in minutes to remove from UTC time to get user time"""
        with open("/data/knowledge/global_context.txt", 'r') as f:
            template = Template(f.read())
            timestamp = datetime.utcnow()
            timestamp -= timedelta(minutes=timezone_offset)
            return template.render(weekday=timestamp.strftime("%A"),
                                   datetime=timestamp.strftime("%d %B %Y"),
                                   time=timestamp.strftime("%H:%M"))

