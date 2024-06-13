
import json
from typing import List

from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT
        

class StanzaDividerStep(WorkflowStep):
    logger_prefix = "StanzaDividerStep :: "

    determine_poem_stanzas_filename = "instructions/determine_poem_stanza.mpt"


    @property
    def definition_for_system(self):
        return "Determine topic of each stanza of a poem."

    @property
    def input_keys(self):
        return ['poem_topic', 'n_stanzas']
    
    @property
    def output_keys(self):
        return ['stanza_topic']

    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int, task_name_for_system: str, session_id:str):
        try: 
            # input keys: poem_topic, n_stanza
            print(f"🔵parameter: {parameter}")
            poem_topic = parameter['poem_topic']
            n_stanzas = parameter['n_stanzas']
            print("🔵")
            determine_poem_stanzas_mpt = MPT(StanzaDividerStep.determine_poem_stanzas_filename, poem_topic=poem_topic, n_stanzas=n_stanzas,
                                             learned_instructions=learned_instructions, past_validated_steps_results=past_validated_steps_results)
            print("🔵🔵")
            responses = determine_poem_stanzas_mpt.run(user_id=user_id, temperature=0, max_tokens=100, user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system)
            response = responses[0].strip()
            print("🔵🔵🔵")
            topics_list = response.split("\n")
            return [{'stanza_topic': topic} for topic in topics_list]
        
            # output keys: 'stanza_topic'
        except Exception as e:
            raise Exception(f"{StanzaDividerStep.logger_prefix} :: execute :: {e}")
