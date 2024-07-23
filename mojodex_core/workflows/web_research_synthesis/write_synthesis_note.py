from typing import List
from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT


class WriteSynthesisNoteStep(WorkflowStep):

    synthesize_mpt_filename = 'mojodex_core/workflows/web_research_synthesis/synthesis.mpt'

    def _synthesize(self, sources_notes: List[str], search_topic:str, user_id: str, user_task_execution_pk: int, task_name_for_system: str):
        try:
            synthesis_mpt = MPT(self.synthesize_mpt_filename, notes=sources_notes, search_topic=search_topic)
            with open('/data/synthesis_prompt.txt', 'w') as f:
                f.write(synthesis_mpt.prompt)
            synthesis_note = synthesis_mpt.run(user_id=user_id, temperature=0, max_tokens=4000,
                                               user_task_execution_pk=user_task_execution_pk,
                                               task_name_for_system=task_name_for_system)
            return synthesis_note
        except Exception as e:
            raise Exception(f"_synthesize :: {e}")

    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict, past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int, task_name_for_system: str, session_id: str):

        sources_notes = parameter['notes']
        sources_urls = parameter['sources_urls']
        search_topic = initial_parameters['research_subject']

        synthesis_note = self._synthesize(sources_notes, search_topic, user_id, user_task_execution_pk, task_name_for_system)

        urls = sources_urls.strip().split('\n')
        synthesis_note += f"\n\nSources:\n"
        synthesis_note += '\n'.join([f"[{url}]({url})" for url in urls if url])
        
        return [{'synthesis_note': synthesis_note}]