
from models.session.assistant_message_context.chat_context import ChatContext
from models.session.assistant_message_state.general_chat_state import GeneralChatState
from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from app import placeholder_generator
from models.session.assistant_message_generators.task_enabled_assistant_response_generator import TaskEnabledAssistantResponseGenerator


class GeneralChatResponseGenerator(TaskEnabledAssistantResponseGenerator):
    logger_prefix = "GeneralChatResponseGenerator :: "
    # TODO: with @kelly check how to mpt-ize this
    prompt_template_path = "/data/prompts/home_chat/run.txt"
    user_message_start_tag, user_message_end_tag = "<message_to_user>", "</message_to_user>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, user, session_id, user_messages_are_audio, running_user_task_execution_pk):
        try:
            chat_state = GeneralChatState(running_user_task_execution_pk)
            chat_context= ChatContext(user, session_id, user_messages_are_audio, chat_state)
            super().__init__(GeneralChatResponseGenerator.prompt_template_path, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, chat_context, llm_call_temperature=1)
        except Exception as e:
            raise Exception(f"{GeneralChatResponseGenerator.logger_prefix} __init__ :: {e}")

    def _get_message_placeholder(self):
        return f"{GeneralChatResponseGenerator.user_message_start_tag}{placeholder_generator.mojo_message}{GeneralChatResponseGenerator.user_message_end_tag}"
    
    def _manage_response_tags(self, response):
        try:
            if self.user_message_start_tag in response:
                text = AssistantMessageGenerator.remove_tags_from_text(response, self.user_message_start_tag, self.user_message_end_tag)
                return {"text": text, 'text_with_tags': response}
            return self._manage_response_task_tags(response)
        except Exception as e:
            raise Exception(f"{GeneralChatResponseGenerator.logger_prefix} _manage_response_tags :: {e}")

    def __spot_task_pk(self, response):
        try:
            if self.task_pk_end_tag in response:
                task_pk = response.split(self.task_pk_start_tag)[1].split(self.task_pk_end_tag)[0]
                if task_pk.strip().lower() == "null":
                    return True, None
                task_pk = int(task_pk.strip())

                # run specific task prompt
                return True, task_pk
            return False, None
        except Exception as e:
            raise Exception(f"__spot_task_pk :: {e}")

    def generate_message(self):
        try:
            message = super().generate_message()
            if message:
                return message
            else:
                return self.generate_message()
        except Exception as e:
            raise Exception(f"{GeneralChatState.logger_prefix} generate_message :: {e}")

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
           self._stream_no_tag_text(partial_text)
        else:
            if not self.context.state.running_task_set:
                task_pk_spotted, task_pk = self.__spot_task_pk(partial_text)
                if task_pk_spotted:
                    running_task_pk = self.running_task.task_pk if self.running_task else None
                    if task_pk is not None and task_pk != running_task_pk:
                        self.context.state.set_running_task(task_pk, self.context.session_id)
                        # TASK SPOTTED
                        return True # Stop the stream
                    elif task_pk is None and self.running_task is not None:
                        # TASK ENDED
                        self.context.state.set_running_task(None)
            
            if self.user_message_start_tag in partial_text:
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text, self.user_message_start_tag, self.user_message_end_tag)
                self.mojo_message_token_stream_callback(text)
            
            self._stream_task_tokens(partial_text)