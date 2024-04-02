from models.workflows.step import WorkflowStep
from typing import List

from mojodex_core.llm_engine.mpt import MPT
        

class StanzaWriterStep(WorkflowStep):

    write_poem_stanza_filename = "instructions/write_poem_stanza.mpt"

    @property
    def description(self):
        return "Write stanza of a poem"

    @property
    def input_keys(self):
        return ['stanza_topic']
    
    @property
    def output_keys(self):
        return ['stanza']
    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, past_validated_steps_results: List[dict], user_id: str):
        try: 
            # input keys: stanza_topic
            stanza_topic = parameter['stanza_topic']
            poem_topic = initial_parameter['poem_topic']
            write_poem_stanza_mpt = MPT(StanzaWriterStep.write_poem_stanza_filename, poem_topic=poem_topic, stanza_topic=stanza_topic,
                                        learned_instructions=learned_instructions, past_validated_steps_results=past_validated_steps_results)
            responses = write_poem_stanza_mpt.run(user_id=user_id, temperature=0, max_tokens=1000)
            stanza = responses[0].strip().lower()
            return [{'stanza': stanza}]
        
            # output keys: 'stanza'
        except Exception as e:
            raise Exception(f"execute :: {e}")
