from datetime import datetime

from mojodex_core.llm_engine.mpt import MPT


class KnowledgeManager:

    @property
    def mojodex_knowledge(self):
        return MPT("mojodex_core/instructions/mojodex_knowledge.mpt").prompt

    @property
    def global_context_knowledge(self):
        timestamp = datetime.now()  # TODO : change timezone to user's one
        return MPT("mojodex_core/instructions/global_context.mpt", weekday=timestamp.strftime("%A"),
                   datetime=timestamp.strftime("%d %B %Y"),
                   time=timestamp.strftime("%H:%M")).prompt

knowledge_manager = KnowledgeManager()