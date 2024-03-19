from models.session.assistant_message_state.chat_state import ChatState
from models.session.assistant_message_context.chat_context import ChatContext
from models.session.assistant_message_generators.assistant_response_generator import AssistantResponseGenerator
from app import llm, llm_conf, llm_backup_conf

class WorkflowAssistantResponseGenerator(AssistantResponseGenerator):
    prompt_template_path = "/data/prompts/workflow/run.txt"
    message_generator = llm(llm_conf,label="CHAT", llm_backup_conf = llm_backup_conf)

    def __init__(self, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, mojo_message_token_stream_callback, user, session_id, user_messages_are_audio, running_user_workflow_execution_pk):
        self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
        chat_state = ChatState()
        chat_context= ChatContext(user, session_id, user_messages_are_audio, chat_state)
        super().__init__(self.prompt_template_path, self.message_generator, chat_context, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, 0)


    def _get_message_placeholder(self):
        """
        Get the message placeholder
        """
        raise NotImplementedError

  
    def _manage_response_tags(self, response):
        """
        Remove and managed tags from the response
        """
        raise NotImplementedError


    def _token_callback(self, partial_text):
        """
        Token callback
        """
        raise NotImplementedError

