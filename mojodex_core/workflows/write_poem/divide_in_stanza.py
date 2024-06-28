
from typing import List

from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT
        

class StanzaDividerStep(WorkflowStep):
    logger_prefix = "StanzaDividerStep :: "

    determine_poem_stanzas_filename = "mojodex_core/workflows/write_poem/determine_poem_stanza.mpt"
    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int, task_name_for_system: str, session_id:str):
        try: 
            # input keys: poem_topic, n_stanza
            poem_topic = parameter['poem_topic']
            n_stanzas = parameter['n_stanzas']

            determine_poem_stanzas_mpt = MPT(StanzaDividerStep.determine_poem_stanzas_filename, poem_topic=poem_topic, n_stanzas=n_stanzas,
                                             learned_instructions=learned_instructions, past_validated_steps_results=past_validated_steps_results)
            responses = determine_poem_stanzas_mpt.run(user_id=user_id, temperature=0, max_tokens=100, user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system)
            response = responses[0].strip()
            topics_list = response.split("\n")
            return [{'stanza_topic': topic} for topic in topics_list]
        
            # output keys: 'stanza_topic'
        except Exception as e:
            raise Exception(f"{StanzaDividerStep.logger_prefix} :: execute :: {e}")
