from background_logger import BackgroundLogger
from mojodex_core.json_loader import json_decode_retry

from app import send_admin_error_email, on_json_error
from models.events.events_generator import EventsGenerator
from models.knowledge.knowledge_collector import KnowledgeCollector

from mojodex_core.llm_engine.mpt import MPT


class DailyNotificationsGenerator(EventsGenerator):
    logger_prefix = "DailyNotificationsGenerator::"
    daily_notification_text_mpt_filename = "instructions/daily_notification_text.mpt"

    def __init__(self):
        self.logger = BackgroundLogger(
            f"{DailyNotificationsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, mojo_knowledge, users):
        try:
            self.logger.info(" generate_events")
            for user in users:
                user_id = user["user_id"]
                try:
                    global_context = KnowledgeCollector.get_global_context_knowledge(
                        user["user_timezone_offset"])
                    notification_json = self.__generate_notif_text(mojo_knowledge, global_context,
                                                                   user_id, user["user_name"],
                                                                   user["user_company_description"],
                                                                   user["user_goal"],
                                                                   user["new_todos_today"],
                                                                   user["language"])
                    notification_title, notification_body = notification_json[
                        "title"], notification_json["message"]
                    data = {"user_id": user_id, "type": "todos"}

                    self.send_event(user_id, message={"title": notification_title, "body": notification_body},
                                    event_type="daily_notification", data=data)
                except Exception as e:
                    send_admin_error_email(
                        f"{self.logger.name} : Error preparing notification for user {user_id}: {e}")
        except Exception as e:
            send_admin_error_email(
                f"{self.logger.name} : Error preparing notifications: {e}")

    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def __generate_notif_text(self, mojo_knowledge, global_context, user_id, username, user_company_knowledge,
                              user_business_goal,
                              new_todos_today, language, retry=2):
        try:
            self.logger.info(f"generate_notif_text for user {user_id}")
            daily_notification_text = MPT(DailyNotificationsGenerator.daily_notification_text_mpt_filename,
                                          mojo_knowledge=mojo_knowledge,
                                          global_context=global_context,
                                          username=username,
                                          user_company_knowledge=user_company_knowledge,
                                          user_business_goal=user_business_goal,
                                          new_todos_today=new_todos_today,
                                          language=language
                                          )

            # TODO: @kelly why doing this?
            # write the prompt in /data/daily_notif_prompt.txt
            with open("/data/daily_notif_prompt.txt", "w") as f:
                f.write(daily_notification_text.prompt)
            notification_message = daily_notification_text.run(user_id=user_id,
                                                               temperature=0,
                                                               json_format=True,
                                                               max_tokens=50)[0]

            return notification_message
        except Exception as e:
            raise Exception(f"generate_notif_text: " + str(e))
