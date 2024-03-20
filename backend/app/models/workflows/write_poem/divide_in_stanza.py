from models.workflows.step import WorkflowStep
import json
from typing import List

from mojodex_core.llm_engine.mpt import MPT
        

class StanzaDividerStep(WorkflowStep):
    logger_prefix = "StanzaDividerStep :: "

    determine_poem_stanzas_filename = "instructions/determine_poem_stanza.mpt"

    @property
    def description(self):
        return "Determine topic of each stanza."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['poem_topic', 'n_stanzas'], output_keys=['stanza_topic'])

    
    def _execute(self, parameter: dict, initial_parameter: dict, history: List[dict]):
        try: 
            # input keys: poem_topic, n_stanza
            poem_topic = parameter['poem_topic']
            n_stanzas = parameter['n_stanzas']
            determine_poem_stanzas_mpt = MPT(StanzaDividerStep.determine_poem_stanzas_filename, poem_topic=poem_topic, n_stanzas=n_stanzas)

            responses = determine_poem_stanzas_mpt.run(user_id="fake", temperature=0, max_tokens=100)
            response = responses[0].strip().lower()
            topics_list = response.split("\n")
            return [{'stanza_topic': topic} for topic in topics_list]
        
            # output keys: 'stanza_topic'
        except Exception as e:
            raise Exception(f"{StanzaDividerStep.logger_prefix} :: execute :: {e}")
