from datetime import datetime
from app import db
from mojodex_core.entities import MdUser, MdCompany
from jinja2 import Template


class KnowledgeManager:
    mojo_knowledge_file = "mojodex_core/prompts/knowledge/mojo_knowledge.txt"
    global_context_file = "mojodex_core/prompts/knowledge/global_context.txt"
    @staticmethod
    def get_mojo_knowledge():
        with open(KnowledgeManager.mojo_knowledge_file, 'r') as f:
            return f.read()

    @staticmethod
    def get_user_knowledge(user_id):
        user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
        return user.summary

    @staticmethod
    def get_user_name(user_id):
        user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
        return user.name

    @staticmethod
    def get_user_company_knowledge(user_id):
        user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
        return user.company_description

    @staticmethod
    def get_global_context_knowledge():
        with open(KnowledgeManager.global_context_file, 'r') as f:
            template = Template(f.read())
            timestamp = datetime.now()  # TODO : change timezone to user's one
            return template.render(weekday=timestamp.strftime("%A"),
                                   datetime=timestamp.strftime("%d %B %Y"),
                                   time=timestamp.strftime("%H:%M"), )