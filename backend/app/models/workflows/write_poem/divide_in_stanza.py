from models.workflows.step import WorkflowStep
import json
from typing import List

from mojodex_core.llm_engine.mpt import MPT
        

class StanzaDividerStep(WorkflowStep):
    logger_prefix = "StanzaDividerStep :: "

    determine_poem_stanzas_filename = "instructions/determine_poem_stanza.mpt"


    @property
    def description(self):
        return "Determine topic of each stanza of a poem."

    @property
    def input_keys(self):
        return ['poem_topic', 'n_stanzas']
    
    @property
    def output_keys(self):
        return ['stanza_topic']

    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict], workflow_conversation: str):
        try: 
            # input keys: poem_topic, n_stanza
            poem_topic = parameter['poem_topic']
            n_stanzas = parameter['n_stanzas']
            print(f"🟢 learned_instructions: {learned_instructions}")
            determine_poem_stanzas_mpt = MPT(StanzaDividerStep.determine_poem_stanzas_filename, poem_topic=poem_topic, n_stanzas=n_stanzas,
                                             learned_instructions=learned_instructions, history=history)
            # write determine_poem_stanzas_mpt.prompt into a file
            with open("/data/determine_poem_stanzas_mpt.txt", "w") as f:
                f.write(determine_poem_stanzas_mpt.prompt)
            responses = determine_poem_stanzas_mpt.run(user_id="fake", temperature=0, max_tokens=100)
            response = responses[0].strip().lower()
            topics_list = response.split("\n")
            return [{'stanza_topic': topic} for topic in topics_list]
        
            # output keys: 'stanza_topic'
        except Exception as e:
            raise Exception(f"{StanzaDividerStep.logger_prefix} :: execute :: {e}")
