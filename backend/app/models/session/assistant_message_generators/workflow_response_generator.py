from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from models.session.assistant_message_state.workflow_chat_state import WorkflowChatState
from models.knowledge.knowledge_manager import KnowledgeManager
from models.session.assistant_message_state.chat_state import ChatState
from models.session.assistant_message_context.chat_context import ChatContext
from models.session.assistant_message_generators.assistant_response_generator import AssistantResponseGenerator
from app import llm, llm_conf, llm_backup_conf, placeholder_generator, server_socket

class WorkflowAssistantResponseGenerator(AssistantResponseGenerator):
    prompt_template_path = "/data/prompts/workflows/run.txt"
    message_generator = llm(llm_conf,label="CHAT", llm_backup_conf = llm_backup_conf)
    user_instruction_start_tag, user_instruction_end_tag = "<user_instruction>", "</user_instruction>"
    ask_for_clarification_start_tag, ask_for_clarification_end_tag = "<ask_for_clarification>", "</ask_for_clarification>"
    inform_user_start_tag, inform_user_end_tag = "<inform_user>", "</inform_user>"
    no_go_explanation_start_tag, no_go_explanation_end_tag = "<no_go_explanation>", "</no_go_explanation>"

    def __init__(self, use_message_placeholder, tag_proper_nouns, mojo_message_token_stream_callback, user, session_id, user_messages_are_audio, running_user_workflow_execution_pk):
        self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
        self.use_message_placeholder=use_message_placeholder
        chat_state = WorkflowChatState(running_user_workflow_execution_pk)
        chat_context= ChatContext(user, session_id, user_messages_are_audio, chat_state)
        super().__init__(self.prompt_template_path, self.message_generator, chat_context,tag_proper_nouns, 0)


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
            print(f"🟢 _manage_response_tags: {response}")
            if WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag in response:
                return {"text": AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag,
                                                        WorkflowAssistantResponseGenerator.ask_for_clarification_end_tag)}
                                                        
            elif WorkflowAssistantResponseGenerator.inform_user_start_tag in response:
                self.context.state.running_user_workflow_execution.invalidate_current_run()
                server_socket.start_background_task(self.context.state.running_user_workflow_execution.run)
                return {"text": AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.inform_user_start_tag,
                                                        WorkflowAssistantResponseGenerator.inform_user_end_tag)}
            
            elif WorkflowAssistantResponseGenerator.no_go_explanation_start_tag in response:
                return {"text": AssistantMessageGenerator.remove_tags_from_text(response, WorkflowAssistantResponseGenerator.no_go_explanation_start_tag,
                                                        WorkflowAssistantResponseGenerator.no_go_explanation_end_tag)}
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
                                                    user_workflow_inputs=self.context.state.running_user_workflow_execution.json_inputs,
                                                    # steps_executions=self.context.state.running_user_workflow_execution.steps_executions,
                                                    # current_step=self.context.state.running_user_workflow_execution.current_step_execution,
                                                    audio_message=self.context.user_messages_are_audio,
                                                    tag_proper_nouns=self.tag_proper_nouns
                                                    )
        except Exception as e:
            raise Exception(f"{WorkflowAssistantResponseGenerator.logger_prefix} _render_prompt_from_template :: {e}")


    def _token_callback(self, partial_text):
        """
        Token callback
        """
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
           self._stream_no_tag_text(partial_text)
        else:            
            self._stream_workflow_tokens(partial_text)

    def _stream_no_tag_text(self, partial_text):
        if self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

    def _stream_workflow_tokens(self, partial_text):
        text=None
        if WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, WorkflowAssistantResponseGenerator.ask_for_clarification_start_tag,
                                                        WorkflowAssistantResponseGenerator.ask_for_clarification_end_tag)
        elif WorkflowAssistantResponseGenerator.inform_user_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, WorkflowAssistantResponseGenerator.inform_user_start_tag,
                                                        WorkflowAssistantResponseGenerator.inform_user_end_tag)
        elif WorkflowAssistantResponseGenerator.no_go_explanation_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, WorkflowAssistantResponseGenerator.no_go_explanation_start_tag,
                                                        WorkflowAssistantResponseGenerator.no_go_explanation_end_tag)
        if text and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(text)
