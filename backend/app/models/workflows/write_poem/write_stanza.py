from models.workflows.step import WorkflowStep
import json
from typing import List

from mojodex_core.llm_engine.mpt import MPT
        

class StanzaWriterStep(WorkflowStep):

    write_poem_stanza_filename = "instructions/write_poem_stanza.mpt"

    @property
    def description(self):
        return "Write a stanza."

    def __init__(self, workflow_step):
        super().__init__(workflow_step, input_keys=['stanza_topic'], output_keys=['stanza'])

    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict],  workflow_conversation: str):
        try: 
            # input keys: stanza_topic
            stanza_topic = parameter['stanza_topic']
            poem_topic = initial_parameter['poem_topic']
            write_poem_stanza_mpt = MPT(StanzaWriterStep.write_poem_stanza_filename, poem_topic=poem_topic, stanza_topic=stanza_topic,
                                        learned_instructions=learned_instructions, history=history)
            # write write_poem_stanza_mpt.prompt into a file
            with open("/data/write_poem_stanza_mpt.txt", "w") as f:
                f.write(write_poem_stanza_mpt.prompt)
            responses = write_poem_stanza_mpt.run(user_id="fake", temperature=0, max_tokens=1000)
            stanza = responses[0].strip().lower()
            return [{'stanza': stanza}]
        
            # output keys: 'stanza'
        except Exception as e:
            raise Exception(f"execute :: {e}")
