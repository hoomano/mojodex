from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from models.session.assistant_message_state.workflow_chat_state import WorkflowChatState
from models.knowledge.knowledge_manager import KnowledgeManager
from models.session.assistant_message_context.chat_context import ChatContext
from app import placeholder_generator, server_socket
from app import model_loader
from models.session.assistant_message_generators.task_enabled_assistant_response_generator import \
    TaskEnabledAssistantResponseGenerator


class WorkflowAssistantResponseGenerator(TaskEnabledAssistantResponseGenerator):
    prompt_template_path = "/data/prompts/workflows/run.txt"
    user_instruction_start_tag, user_instruction_end_tag = "<user_instruction>", "</user_instruction>"
    ask_for_clarification_start_tag, ask_for_clarification_end_tag = "<ask_for_clarification>", "</ask_for_clarification>"
    no_go_explanation_start_tag, no_go_explanation_end_tag = "<no_go_explanation>", "</no_go_explanation>"

    def __init__(self, use_message_placeholder, tag_proper_nouns, mojo_message_token_stream_callback, user, session_id, user_messages_are_audio, running_user_workflow_execution_pk):
        chat_state = WorkflowChatState(running_user_workflow_execution_pk)
        chat_context = ChatContext(user, session_id, user_messages_are_audio, chat_state)
        super().__init__(self.prompt_template_path, mojo_message_token_stream_callback,
                 use_message_placeholder, tag_proper_nouns, chat_context, llm_call_temperature=0)


    def _get_message_placeholder(self):
        """
        Get the message placeholder
        """
        return f"{WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag}{placeholder_generator.mojo_message}{WorkflowAssistantResponseGenerator.ask_for_clarification_end_tag}"


    def _handle_placeholder(self):
        try:
            placeholder = None
            if self.use_message_placeholder:
                placeholder = self._get_message_placeholder()
            #elif self.use_draft_placeholder:
                #placeholder = 
            if placeholder:
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"{WorkflowAssistantResponseGenerator.logger_prefix} _handle_placeholder :: {e}")
  
    def _manage_response_tags(self, response):
        """
        Remove and managed tags from the response
        """
        try:
            if WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag in response:
                return {"text": AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag,
                                                        WorkflowAssistantResponseGenerator.ask_for_clarification_end_tag),
                                                        "text_with_tags": response}
                                                        
            elif WorkflowAssistantResponseGenerator.user_instruction_start_tag in response:
                instruction = AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.user_instruction_start_tag,
                                                        WorkflowAssistantResponseGenerator.user_instruction_end_tag)
                self.context.state.running_user_workflow_execution.invalidate_current_step(instruction)
                server_socket.start_background_task(self.context.state.running_user_workflow_execution.run)
                return None
            
            elif WorkflowAssistantResponseGenerator.no_go_explanation_start_tag in response:
                return {"text": AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.no_go_explanation_start_tag,
                                                        WorkflowAssistantResponseGenerator.no_go_explanation_end_tag),
                                                        "text_with_tags": response}
            return {"text": response}
        except Exception as e:
            raise Exception(f"_manage_response_task_tags :: {e}")

    def _render_prompt_from_template(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(self.context.user_id)
            
            return self.prompt_template.render(mojo_knowledge=mojo_knowledge,
                                                    global_context=global_context,
                                                    username=self.context.username,
                                                    user_company_knowledge=user_company_knowledge,
                                                    workflow=self.context.state.running_user_workflow_execution.workflow,
                                                    user_workflow_inputs=self._get_running_user_task_execution_inputs(),
                                                    audio_message=self.context.user_messages_are_audio,
                                                    tag_proper_nouns=self.tag_proper_nouns
                                                    )
        except Exception as e:
            raise Exception(f"{WorkflowAssistantResponseGenerator.logger_prefix} _render_prompt_from_template :: {e}")


    def _stream_task_tokens(self, partial_text):
        text=None
        if WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag,
                                                        WorkflowAssistantResponseGenerator.ask_for_clarification_end_tag)
        elif WorkflowAssistantResponseGenerator.no_go_explanation_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, WorkflowAssistantResponseGenerator.no_go_explanation_start_tag,
                                                        WorkflowAssistantResponseGenerator.no_go_explanation_end_tag)
        if text and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(text)

    def _generate_message_from_prompt(self, prompt):
        """
        Generate a message from a prompt by calling the message generator
        :param prompt: prompt
        :return: generated message
        """
        try:
            my_llm = model_loader.get_main_llm_provider()
            my_llm.max_retries = 10
            my_llm.client.max_retries = 10
            my_llm.client.timeout = 600
            my_llm.client_backup = None
            conversation_list = self.context.state.get_conversation_as_list(self.context.session_id)
            messages = [{"role": "system", "content": prompt}] + conversation_list
            responses = my_llm.invoke(messages, self.context.user_id,
                                                        temperature=0,
                                                        max_tokens=4000,
                                                        label="CHAT",
                                                        stream=True, stream_callback=self._token_callback)

            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"_generate_message_from_prompt:: {e}")