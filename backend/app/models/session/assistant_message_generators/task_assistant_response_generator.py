from models.session.assistant_message_context.chat_context import ChatContext
from models.session.assistant_message_generators.task_enabled_assistant_response_generator import TaskEnabledAssistantResponseGenerator
from models.session.assistant_message_state.task_enabled_chat_state import TaskEnabledChatState


class TaskAssistantResponseGenerator(TaskEnabledAssistantResponseGenerator):
    logger_prefix = "TaskAssistantResponseGenerator :: "
    prompt_template_path = "/data/prompts/tasks/run.txt"
    
    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, user, session_id, user_messages_are_audio, running_user_task_execution_pk):
        try:
            chat_state = TaskEnabledChatState(running_user_task_execution_pk)
            chat_context= ChatContext(user, session_id, user_messages_are_audio, chat_state)
            super().__init__(TaskAssistantResponseGenerator.prompt_template_path, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, chat_context, llm_call_temperature=0)
        except Exception as e:
            raise Exception(f"{TaskAssistantResponseGenerator.logger_prefix} __init__ :: {e}")

    def _get_message_placeholder(self):
        super()._get_task_input_placeholder()

    