from jinja2 import Template
from background_logger import BackgroundLogger
from mojodex_core.mojodex_openai import MojodexOpenAI
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error
from azure_openai_conf import AzureOpenAIConf
from app import send_admin_error_email
from models.events.events_generator import EventsGenerator


class TaskToolExecutionNotificationsGenerator(EventsGenerator):
    logger_prefix = "TaskToolExecutionNotificationsGenerator::"
    notification_text_prompt = "/data/prompts/engagement/notifications/task_tool_execution_notification_text_prompt.txt"
    notification_text_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf,
                                                "TASK_TOOL_NOTIFICATION")

    def __init__(self):
        self.logger = BackgroundLogger(f"{TaskToolExecutionNotificationsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, user_id, knowledge_collector, task_name, task_definition, task_title, task_summary,
                        tool_name, task_tool_association, results, language, user_task_execution_pk):
        try:
            self.logger.info("generate_events")
            try:
                notification_json = self.__generate_notif_text(user_id, knowledge_collector, task_name, task_definition,
                                                              task_title, task_summary,
                                                              tool_name, task_tool_association, results, language,
                                                              user_task_execution_pk)
                notification_title, notification_body = notification_json["title"], notification_json["message"]
                data = {"user_id": user_id,
                        "user_task_execution_pk": str(user_task_execution_pk),
                        "type": "chat"}
                self.send_event(user_id, message={"title": notification_title, "body": notification_body},
                                event_type="task_tool_execution_notification", data=data)
            except Exception as e:
                self.logger.debug(f"Error preparing notification for user {user_id}: {e}")
                send_admin_error_email(f"{self.logger.name} : Error preparing notification for user {user_id}: {e}")
        except Exception as e:
            self.logger.debug(f"Error preparing notification for user {user_id}: {e}")
            send_admin_error_email(f"{self.logger.name} : Error preparing notifications: {e}")

    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def __generate_notif_text(self, user_id, knowledge_collector, task_name, task_definition, task_title, task_summary,
                             tool_name, task_tool_association, results, language, user_task_execution_pk):
        try:
            self.logger.info(f"generate_notif_text")
            with open(TaskToolExecutionNotificationsGenerator.notification_text_prompt, "r") as f:
                template = Template(f.read())

                prompt = template.render(
                    mojo_knowledge=knowledge_collector.mojo_knowledge,
                    global_context=knowledge_collector.global_context,
                    username=knowledge_collector.user_name,
                    user_company_knowledge=knowledge_collector.user_company_knowledge,
                    user_business_goal=knowledge_collector.user_business_goal,
                    task_name=task_name,
                    task_definition=task_definition,
                    task_title=task_title,
                    task_summary=task_summary,
                    tool_name=tool_name,
                    task_tool_association=task_tool_association,
                    results=results,
                    language=language
                )

            # call openai to generate text
            messages = [{"role": "system", "content": prompt}]

            notification_json = \
            TaskToolExecutionNotificationsGenerator.notification_text_generator.chat(messages, user_id,
                                                                                     temperature=1, max_tokens=50,
                                                                                     json_format=True,
                                                                                     user_task_execution_pk=user_task_execution_pk,
                                                                                     task_name_for_system=task_name)[0]

            return notification_json
        except Exception as e:
            raise Exception(f"generate_notif_text: " + str(e))
