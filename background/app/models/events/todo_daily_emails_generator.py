import os
from jinja2 import Template

from mojodex_core.db import with_db_session
from mojodex_core.email_sender.email_service import EmailService

from mojodex_core.entities.user import User
from mojodex_core.entities.user_task_execution import UserTaskExecution
from mojodex_core.knowledge_manager import KnowledgeManager
from models.events.events_generator import EmailEventGenerator
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import on_json_error
from mojodex_core.llm_engine.mpt import MPT


class TodoDailyEmailsGenerator(EmailEventGenerator):

    message_from_mojodex_email = "mojodex_core/mails_templates/message_from_mojodex.html"
    todo_daily_email_text_mpt_filename = "instructions/todo_daily_emails_text_prompt.mpt"
    todo_daily_email_type = "todo_daily_email"

    def __init__(self, user_id):
        self.user_id = user_id
        super().__init__()

    @with_db_session
    def _collect_data(self, db_session):
        try:
            user: User = db_session.query(User).get(self.user_id)

            # User's todo items that are scheduled for today
            today_todo_list = [{"description": todo.description, "related_user_task_execution_title": db_session.query(UserTaskExecution).get(todo.user_task_execution_fk).title} for todo in user.today_todo_list]
            
            # User's todo items that have been rescheduled today
            rescheduled_todos = [{"description": todo.description, "scheduled_date": todo.scheduled_date, "reschedule_justification": todo.scheduling.reschedule_justification,
                                  "related_user_task_execution_title": db_session.query(UserTaskExecution).get(todo.user_task_execution_fk).title} for todo in user.today_rescheduled_todo]

            return user.email, user.datetime_context, user.name, user.company_description, user.goal, user.language_code, today_todo_list, rescheduled_todos
        except Exception as e:
            raise Exception(f"_collect_data: {e}")
            

    def generate_events(self):
        try:
            collected_data = self._collect_data()
            email = collected_data[0]
            email_json = self._generate_emails_text(*collected_data[1:]) # all except email

            subject, body = email_json["subject"], email_json["body"]
         
            with open(TodoDailyEmailsGenerator.message_from_mojodex_email, "r") as f:
                template = Template(f.read())
                body = template.render(mojodex_message=body, mojodex_webapp_url=os.environ["MOJODEX_WEBAPP_URI"],
                                        button_text="View To-do List")
            print(f"🟢 sending email to {email}")
            self.send_event(self.user_id,
                            event_type=TodoDailyEmailsGenerator.todo_daily_email_type,
                            subject=subject,
                            body=body,
                            email_address=email)
                            
           
        except Exception as e:
            print(f"🔴 generate_events: {e}")
            EmailService().send_technical_error_email(
                f"{self.__class__.__name__} : generate_events : Error preparing email to user_id {self.user_id}: {e}")

    @json_decode_retry(retries=3, required_keys=["subject", "body"], on_json_error=on_json_error)
    def _generate_emails_text(self, user_datetime_context, username, user_company_knowledge,
                               user_business_goal, language, today_todo_list, rescheduled_todos):
        try:
            todo_daily_email_text = MPT(TodoDailyEmailsGenerator.todo_daily_email_text_mpt_filename,
                                        mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                        user_datetime_context=user_datetime_context,
                                        username=username,
                                        user_company_knowledge=user_company_knowledge,
                                        user_business_goal=user_business_goal,
                                        todo_list=today_todo_list,
                                        rescheduled_todo_items=rescheduled_todos,
                                        language=language
                                        )
            
            email_message_json = todo_daily_email_text.run(user_id=self.user_id,
                                                           temperature=0,
                                                           max_tokens=4000,
                                                           json_format=True)[0]
            return email_message_json
        except Exception as e:
            raise Exception(f"_generate_emails_text: {e}")
