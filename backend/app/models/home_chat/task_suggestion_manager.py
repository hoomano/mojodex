from mojodex_backend_logger import MojodexBackendLogger


class TaskSuggestionManager:
    logger_prefix = "TaskSuggestionManager::"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"
    task_instruction_start_tag, task_instruction_end_tag = "<task_instruction>", "</task_instruction>"
    task_placeholder_question_start_tag, task_placeholder_question_end_tag = "<task_placeholder_question>", "</task_placeholder_question>"
    task_placeholder_instructions_start_tag, task_placeholder_instructions_end_tag = "<task_placeholder_instructions>", "</task_placeholder_instructions>"

    def __init__(self, session_id, remove_tags_function):
        self.logger = MojodexBackendLogger(f"{TaskSuggestionManager.logger_prefix} -- session_id {session_id}")
        self.remove_tags_function = remove_tags_function

    def manage_task_suggestion_text(self, task_suggestion_text):
        try:
            task_pk = int(self.remove_tags_function(task_suggestion_text, self.task_pk_start_tag, self.task_pk_end_tag))
            response =  {"task_pk": task_pk}
            if self.task_instruction_start_tag in task_suggestion_text:
                task_instruction = self.remove_tags_function(task_suggestion_text, self.task_instruction_start_tag, self.task_instruction_end_tag)
                response["task_instruction"] = task_instruction
            if self.task_placeholder_question_start_tag in task_suggestion_text:
                task_placeholder_question = self.remove_tags_function(task_suggestion_text, self.task_placeholder_question_start_tag, self.task_placeholder_question_end_tag)
                task_placeholder_instructions = self.remove_tags_function(task_suggestion_text, self.task_placeholder_instructions_start_tag, self.task_placeholder_instructions_end_tag)
                response["task_placeholder_question"] = task_placeholder_question
                response["task_placeholder_instructions"] = task_placeholder_instructions
            return response
        except Exception as e:
            raise Exception(f"{TaskSuggestionManager.logger_prefix} :: manage_task_suggestion_text :: {e}")