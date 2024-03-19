from background_logger import BackgroundLogger


class MessageWriter:
    logger_prefix = "MessageWriter ::"
    tool_result_start_tag, tool_result_end_tag = "<tool_results>", "</tool_results>"

    task_tool_message_writer_mpt_filename = "background/app/instructions/task_tool_execution_message_writer.mpt"

    def __init__(self, title_start_tag, title_end_tag, draft_start_tag, draft_end_tag):
        self.logger = BackgroundLogger(f"{MessageWriter.logger_prefix}")
        self.logger.debug(f"__init__")
        self.title_start_tag = title_start_tag
        self.title_end_tag = title_end_tag
        self.draft_start_tag = draft_start_tag
        self.draft_end_tag = draft_end_tag

    def write_message(self, knowledge_collector, task, tool, task_tool_association, conversation, results,
                      language, user_id, session_id, user_task_execution_pk):
        try:
            self.logger.info(f"write_and_send_message")
            message_text = self._write_message(knowledge_collector, task, tool, task_tool_association, conversation,
                                               results, language, user_id, user_task_execution_pk)
            message = {"text": message_text,
                       "text_with_tags": f"{MessageWriter.tool_result_start_tag}{message_text}{MessageWriter.tool_result_end_tag}"}
            return message
        except Exception as e:
            raise Exception(
                f"{self.logger_prefix} write_and_send_message :: {e}")

    def _write_message(self, knowledge_collector, task, tool, task_tool_association, conversation, results, language,
                       user_id, user_task_execution_pk):
        try:
            self.logger.info(f"_write_message")
            task_tool_message_writer = MPT(MessageWriter.task_tool_message_writer_mpt_filename,
                                           mojo_knowledge=knowledge_collector.mojo_knowledge,
                                           global_context=knowledge_collector.global_context,
                                           username=knowledge_collector.user_name,
                                           task=task,
                                           title_start_tag=self.title_start_tag,
                                           title_end_tag=self.title_end_tag,
                                           draft_start_tag=self.draft_start_tag,
                                           draft_end_tag=self.draft_end_tag,
                                           tool=tool,
                                           task_tool_association=task_tool_association,
                                           conversation=conversation,
                                           results=results,
                                           language=language
                                           )

            responses = task_tool_message_writer.run(user_id,
                                                     temperature=0,
                                                     max_tokens=3000,
                                                     user_task_execution_pk=user_task_execution_pk,
                                                     task_name_for_system=task.name_for_system,
                                                     )

            response = responses[0].strip()
            return response
        except Exception as e:
            raise Exception(f"_write_message :: {e}")
