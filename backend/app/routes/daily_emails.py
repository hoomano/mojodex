import os


import requests
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from sqlalchemy import func, text, extract, case
from sqlalchemy.sql.functions import coalesce

from mojodex_core.mail import send_admin_email, admin_email_receivers
from datetime import datetime, timedelta

class DailyEmails(Resource):
    reminder_email_type="reminder_email"
    summary_email_type="summary_email_type"


    def post(self):
        if not request.is_json:
            log_error(f"Error sending daily emails : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
           secret = request.headers['Authorization']
           if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
               log_error(f"Error sending daily emails : Authentication error : Wrong secret", notify_admin=True)
               return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
           log_error(f"Error sending daily emails : Missing Authorization secret in headers", notify_admin=True)
           return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json['datetime']
            n_emails = min(50, int(request.json["n_emails"])) if "n_emails" in request.json else 50
            offset = int(request.json["offset"]) if "offset" in request.json else 0

        except KeyError:
            log_error(f"Error sending daily emails : Missing datetime in body", notify_admin=True)
            return {"error": f"Missing datetime in body"}, 400

        try:
            # select first n_emails users
            # today_morning = today at 00:00:00
            today_morning = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            n_meeting_minutes_subquery = (db.session.query(
                MdUserTask.user_id.label('user_id'),
                MdUserTaskExecution.user_task_fk,
                func.count(MdUserTaskExecution.user_task_execution_pk).label('today_meeting_minutes_counts'))
                                          .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                                          .join(MdTask, MdUserTask.task_fk == MdTask.task_pk)
                                          .join(MdUser, MdUserTask.user_id == MdUser.user_id)
                                          .filter(MdTask.name_for_system == 'prepare_meeting_minutes',
                                                  func.timezone(
                                                      text(f'md_user.timezone_offset * interval \'1 minute\''),
                                                                MdUserTaskExecution.start_date) >= today_morning,
                                                  MdUserTaskExecution.start_date.isnot(None))
                                          .group_by(MdUserTaskExecution.user_task_fk, MdUserTask.user_id)
                                          ).subquery()

            #  subquery to get the latest meeting minutes date for each user
            # (we will filter those which last meeting minutes date is <= 3 days)
            last_meeting_minutes_date_subquery = (db.session.query(
                MdUserTask.user_id.label('user_id'),
                func.max(MdUserTaskExecution.start_date).label('latest_meeting_minutes_date'))
                                                  .join(MdUserTask,
                                                        MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                                                  .join(MdTask, MdUserTask.task_fk == MdTask.task_pk)
                                                  .filter(MdTask.name_for_system == 'prepare_meeting_minutes',
                                                          MdUserTaskExecution.start_date.isnot(None))
                                                  .group_by(MdUserTask.user_id)
                                                  ).subquery()
            three_days_ago = today_morning - timedelta(days=3)

            # Create a subquery to get the user ids who received a reminder_email the day before yesterday
            day_before_yesterday = today_morning - timedelta(days=2)

            reminder_email_day_before_yesterday_subquery = (db.session.query(MdUser.user_id.label('user_id'))
                                                            .join(MdEvent, MdUser.user_id == MdEvent.user_id)
                                                            .filter(MdEvent.event_type == DailyEmails.reminder_email_type,
                                                                    MdEvent.creation_date >= day_before_yesterday,
                                                                    MdEvent.creation_date < day_before_yesterday + timedelta(
                                                                        days=1))
                                                            .group_by(MdUser.user_id)
                                                            ).subquery()

            # Create a subquery to get the user ids who received a reminder_email yesterday
            yesterday = today_morning - timedelta(days=1)
            reminder_email_yesterday_subquery = (db.session.query(MdUser.user_id.label('user_id'))
                                                 .join(MdEvent, MdUser.user_id == MdEvent.user_id)
                                                 .filter(MdEvent.event_type == DailyEmails.reminder_email_type,
                                                         MdEvent.creation_date >= yesterday,
                                                         MdEvent.creation_date < yesterday + timedelta(days=1))
                                                 .group_by(MdUser.user_id)
                                                 ).subquery()

            # subquery to count the md_process created since today morning for each user, then we join this subquery in the main query.
            process_count_subquery = (db.session.query(
                MdUser.user_id.label('user_id'),
                func.count(MdProcess.process_pk).label('process_count_since_today'))
                                        .join(MdUserTask, MdUser.user_id == MdUserTask.user_id)
                                      .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                                      .join(MdFollowUp,
                                            MdFollowUp.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)
                                      .join(MdProcess, MdProcess.follow_up_fk == MdFollowUp.follow_up_pk)
                                      .filter(MdProcess.creation_date >= today_morning)
                                      .group_by(MdUser.user_id)
                                      ).subquery()

            # Create a subquery to get the 3 last md_followup.description with proactive=True created
            # Window Function to rank rows within a user's follow ups partitioned by user_id, ordered by creation_date descending
            ranked_proactive_followup_subquery = (
                db.session.query(
                    MdUserTask.user_id.label('user_id'),
                    MdFollowUp.description.label("proactive_followup_description"),
                    func.row_number()
                    .over(partition_by=MdUserTask.user_id, order_by=MdFollowUp.creation_date.desc())
                    .label("followup_rank"),
                )
                .join(MdUserTaskExecution,
                      MdFollowUp.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk)
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)
                .filter(MdFollowUp.proactive == True)
                .subquery()
            )

            # Filter the subquery to only include the top 3 ranked follow up descriptions for each user
            filtered_proactive_followup_subquery = (
                db.session.query(
                    ranked_proactive_followup_subquery.c.user_id.label('user_id'),
                    ranked_proactive_followup_subquery.c.proactive_followup_description,
                )
                .filter(ranked_proactive_followup_subquery.c.followup_rank <= 3)
                .subquery()
            )

            # Aggregate the descriptions into an array
            grouped_proactive_followups_subquery = (
                db.session.query(
                    filtered_proactive_followup_subquery.c.user_id.label('user_id'),
                    func.array_agg(
                        filtered_proactive_followup_subquery.c.proactive_followup_description
                    ).label("last_three_proactive_followups"),
                )
                .group_by(filtered_proactive_followup_subquery.c.user_id)
            ).subquery()

            # Subquery for user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("user_lang_name_for_user"),
                )
                .join(MdTask, MdTask.task_pk == MdTaskDisplayedData.task_fk)
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk)
                .join(MdUser, MdUser.user_id == MdUserTask.user_id)
                .filter(MdTaskDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery for 'en'
            en_subquery = (
                db.session.query(
                    MdTaskDisplayedData.task_fk.label("task_fk"),
                    MdTaskDisplayedData.name_for_user.label("en_name_for_user"),
                )
                .filter(MdTaskDisplayedData.language_code == "en")
                .subquery()
            )

            # subquery to find the first represented task in user_task, but no execution
            enabled_not_executed_task_subquery = (
                db.session.query(
                    MdUserTask.user_id.label('user_id'),
                    coalesce(user_lang_subquery.c.user_lang_name_for_user, en_subquery.c.en_name_for_user).label(
                        "first_enabled_not_executed_task_name")
                )
                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk)
                .outerjoin(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk)
                .outerjoin(user_lang_subquery, MdTask.task_pk == user_lang_subquery.c.task_fk)
                .outerjoin(en_subquery, MdTask.task_pk == en_subquery.c.task_fk)
                .filter(MdUserTask.enabled.is_(True))
                .group_by(
                    MdUserTask.user_id, 
                    user_lang_subquery.c.user_lang_name_for_user, 
                    en_subquery.c.en_name_for_user
                )
                .having(func.count(MdUserTaskExecution.user_task_execution_pk) == 0)
            ).subquery()

            # select first n_notifications users and their associated number of meeting recaps today
            results = db.session.query(MdUser.user_id, MdUser.email, MdUser.name, MdUser.company_description,
                                       MdUser.timezone_offset, MdUser.goal, MdUser.language_code,
                                       func.coalesce(
                                            n_meeting_minutes_subquery.c.today_meeting_minutes_counts, 0
                                        ).label("n_meeting_minutes_today"),
                                       case((reminder_email_yesterday_subquery.c.user_id.is_(None), False),
                                            else_=True).label(
                                           "received_reminder_email_yesterday"),
                                       case((reminder_email_day_before_yesterday_subquery.c.user_id.is_(None), False),
                                            else_=True).label(
                                           "reminder_email_day_before_yesterday"),
                                       func.coalesce(process_count_subquery.c.process_count_since_today, 0).label("n_processes_created_today"),
                                       grouped_proactive_followups_subquery.c.last_three_proactive_followups.label("last_three_proactive_followups"),
                                       enabled_not_executed_task_subquery.c.first_enabled_not_executed_task_name.label("first_enabled_not_executed_task_name")
                                       ) \
                .distinct(MdUser.user_id) \
                .outerjoin(n_meeting_minutes_subquery, MdUser.user_id == n_meeting_minutes_subquery.c.user_id) \
                .outerjoin(reminder_email_yesterday_subquery,
                           MdUser.user_id == reminder_email_yesterday_subquery.c.user_id) \
                .outerjoin(reminder_email_day_before_yesterday_subquery,
                           MdUser.user_id == reminder_email_day_before_yesterday_subquery.c.user_id) \
                .outerjoin(grouped_proactive_followups_subquery,
                           MdUser.user_id == grouped_proactive_followups_subquery.c.user_id, ) \
                .outerjoin(process_count_subquery, MdUser.user_id == process_count_subquery.c.user_id) \
                .outerjoin(enabled_not_executed_task_subquery,
                           MdUser.user_id == enabled_not_executed_task_subquery.c.user_id) \
                .join(last_meeting_minutes_date_subquery,
                            MdUser.user_id == last_meeting_minutes_date_subquery.c.user_id) \
                .filter(last_meeting_minutes_date_subquery.c.latest_meeting_minutes_date >= three_days_ago) \
                .filter(MdUser.timezone_offset != None)\
                .filter(extract("hour", text("NOW() - md_user.timezone_offset * interval \'1 minute\'")) >= int(os.environ.get("DAILY_EMAIL_TIME", 17))) \
                .filter(extract("hour", text("NOW() - md_user.timezone_offset * interval \'1 minute\'")) < int(os.environ.get("DAILY_EMAIL_TIME", 17))+1) \
                .order_by(MdUser.user_id).offset(offset).limit(n_emails).all()

            results = [result._asdict() for result in results]

            users = [{"user_id": row["user_id"],
                      "email": row["email"],
                      "user_name": row["name"],
                      "user_company_description": row["company_description"],
                      "user_timezone_offset": row["timezone_offset"],
                      "user_goal": row["goal"],
                      "language": row["language_code"] if row["language_code"] else "en",
                      "n_meeting_minutes_today": row["n_meeting_minutes_today"],
                      "received_reminder_email_yesterday": row["received_reminder_email_yesterday"],
                      "received_reminder_email_the_day_before_yesterday": row["reminder_email_day_before_yesterday"],
                      "n_processes_created_today": row["n_processes_created_today"],
                      "last_three_proactive_followups": row["last_three_proactive_followups"],
                      "first_enabled_not_executed_task_name": row["first_enabled_not_executed_task_name"],
                      } for row in results]
            # no meeting minutes today, already received a reminder yesterday and the day before yesterday => send admin email
            users_needing_admin_email = [user for user in users if user["n_meeting_minutes_today"] == 0 and user[
                "received_reminder_email_yesterday"] and user["received_reminder_email_the_day_before_yesterday"]]
            # others = users - users_needing_admin_email
            user_needing_email = [user for user in users if user not in users_needing_admin_email]

            for user in users_needing_admin_email:
                user_id, email = user["user_id"], user["email"]
                try:
                    send_admin_email(f"User engagement", admin_email_receivers,
                                     f"User {user_id} with email {email} has done no meeting minutes for the last 2 days.")
                except Exception as e:
                    log_error(f"Error sending daily notification to user {user_id}: {e}", notify_admin=True)

            # send backend for preparing email text
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/events_generation"
            pload = {"datetime": datetime.now().isoformat(), "event_type": "daily_emails", "data": user_needing_email}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(f"Error while calling background events_generation : {internal_request.json()}")

            # return list of user_ids
            return {"user_ids": [user["user_id"] for user in users]}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error sending daily emails : {e}", notify_admin=True)
            return {"error": f"Error sending daily emails : {e}"}, 500
