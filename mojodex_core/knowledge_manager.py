from mojodex_core.llm_engine.mpt import MPT


class KnowledgeManager:

    @property
    def mojodex_knowledge(self):
        return MPT("mojodex_core/instructions/mojodex_knowledge.mpt").prompt


knowledge_manager = KnowledgeManager()