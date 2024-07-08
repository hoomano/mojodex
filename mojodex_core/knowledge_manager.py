from mojodex_core.llm_engine.mpt import MPT

class KnowledgeManager:

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KnowledgeManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    @property
    def mojodex_knowledge(self):
        return MPT("mojodex_core/instructions/mojodex_knowledge.mpt").prompt
