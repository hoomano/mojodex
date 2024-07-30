from mojodex_core.db import with_db_session
from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.workflows.doc_gen_workflow.chapter import Chapter

from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.entities.user import User
class ChaptersToDocStep(WorkflowStep):

    chapters_to_doc_mpt_filename = "mojodex_core/workflows/doc_gen_workflow/chapters_to_doc.mpt"

    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict,
                 past_validated_steps_results: list, user_id: str, user_task_execution_pk: int,
                 task_name_for_system: str, session_id: str):
        try:
            chapters = parameter['chapters']


            username, user_datetime_context = self._load_user_details(user_id)

            
                
            chapters_to_doc_mpt = MPT(ChaptersToDocStep.chapters_to_doc_mpt_filename, 
                                    transcription=past_validated_steps_results[0]['result'][0]['transcription'],
                                    chapters_outline=chapters,
                                    mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                    user_datetime_context=user_datetime_context,
                                    username=username)
            
            response = chapters_to_doc_mpt.run(
                user_id=user_id,
                temperature=0,
                max_tokens=4000,
                user_task_execution_pk=user_task_execution_pk,
                task_name_for_system=task_name_for_system,
            )
            
            return [{'doc': response.strip()}]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _execute: {e}")
        
        
    @with_db_session
    def _load_user_details(self, user_id, db_session):
        try:
            user: User = db_session.query(User).get(user_id)

            return user.name, user.datetime_context
        except Exception as e:
            raise Exception(f"_load_user_details :: {e}")    