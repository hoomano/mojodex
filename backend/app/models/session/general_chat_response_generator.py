
from models.session.task_enabled_assistant_response_generator import TaskEnabledChatContext, TaskEnabledChatState
from models.session.assistant_response_generator import TaskEnabledAssistantResponseGenerator
from app import placeholder_generator, db
from db_models import *
from sqlalchemy.orm.attributes import flag_modified

class GeneralChatState(TaskEnabledChatState):

    def __init__(self, running_user_task_execution_pk):
        super().__init__(running_user_task_execution_pk)
        self.running_task_set = False

    def set_running_task(self, task_pk):
        try:
            self.running_task_set = True
            if task_pk is not None:
                self.running_task, self.running_task_displayed_data, self.running_user_task = db.session.query(MdTask, MdTaskDisplayedData, MdUserTask)\
                    .join(MdTaskDisplayedData, MdTask.task_pk == MdTaskDisplayedData.task_fk)\
                    .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk)\
                    .filter(MdTask.task_pk == task_pk).first()
                # create user_task_execution
                self._create_user_task_execution()
                self._associate_previous_user_message()
            else:
                self.running_task, self.running_task_displayed_data, self.running_user_task, self.running_user_task_execution = None, None, None, None
        except Exception as e:
            raise Exception(f"__set_running_task :: {e}")
        
    def _get_empty_json_input_values(self):
        try:
            empty_json_input_values = []
            for input in self.running_task_displayed_data.json_input:
                input["value"] = None
                empty_json_input_values.append(input)
            return empty_json_input_values
        except Exception as e:
            raise Exception(f"_get_empty_json_input_values :: {e}")
        
    def _create_user_task_execution(self):
        try:
            empty_json_input_values = self._get_empty_json_input_values()
           
            task_execution = MdUserTaskExecution(user_task_fk=self.running_user_task.user_task_pk, start_date=datetime.now(),
                                                 json_input_values=empty_json_input_values, session_id=self.session_id)
            db.session.add(task_execution)
            db.session.commit()
            self.running_user_task_execution = task_execution
        except Exception as e:
            raise Exception(f"_create_user_task_execution :: {e}")

    def _associate_previous_user_message(self):
        try:
            print(f"__associate_previous_user_message")
            from models.session.session import Session as SessionModel
            previous_user_message = db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).filter(
                MdMessage.sender == SessionModel.user_message_key).order_by(MdMessage.message_date.desc()).first()
            if previous_user_message:
                new_message = previous_user_message.message

                new_message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
                previous_user_message.message = new_message
                flag_modified(previous_user_message, "message")
                db.session.commit() 
        except Exception as e:
            raise Exception(f"__associate_previous_user_message :: {e}")
        
    

class GeneralChatResponseGenerator(TaskEnabledAssistantResponseGenerator):
    user_message_start_tag, user_message_end_tag = "<user_message>", "</user_message>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    def __init__(self, prompt_template_path, message_generator, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, user, session_id, origin, user_messages_are_audio, running_user_task_execution_pk):
        chat_state = GeneralChatState(running_user_task_execution_pk)
        chat_context= TaskEnabledChatContext(user, session_id, origin, user_messages_are_audio, chat_state)
        super().__init__(prompt_template_path, message_generator, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, chat_context)


    @property
    def llm_temperature(self):
        return 0 if self.running_task else 1


    def _get_message_placeholder(self):
        return f"{GeneralChatResponseGenerator.user_message_start_tag}{placeholder_generator.mojo_message}{GeneralChatResponseGenerator.user_message_end_tag}"
    
    def _manage_response_tags(self, response):
        if self.user_message_start_tag in response:
            text = self.remove_tags_from_text(response, self.user_message_start_tag, self.user_message_end_tag)
            return {"text": text, 'text_with_tags': response}
        self._manage_response_task_tags(response)

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

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
           self._stream_no_tag_text(partial_text)
        else:
            if not self.chat_context.state.running_task_set:
                task_pk_spotted, task_pk = self.__spot_task_pk(partial_text)
                if task_pk_spotted:
                    running_task_pk = self.running_task.task_pk if self.running_task else None
                    if task_pk is not None and task_pk != running_task_pk:
                        self.chat_context.state.set_running_task(task_pk)
                        print("TASK SPOTTED")
                        return True # Stop the stream
                    elif task_pk is None and self.running_task is not None:
                        print("END OF TASK")
                        self.__set_running_task(None)
            
            if self.user_message_start_tag in partial_text:
                text = self.remove_tags_from_text(partial_text, self.user_message_start_tag, self.user_message_end_tag)
                self.mojo_message_token_stream_callback(text)
            
            self._stream_task_tokens(partial_text)