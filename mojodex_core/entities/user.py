


from functools import cached_property
from sqlalchemy import and_, extract, func, text
from mojodex_core.entities.db_base_entities import MdTodo, MdTodoScheduling, MdUser, MdUserTask, MdUserTaskExecution, MdUserVocabulary
from sqlalchemy.orm import object_session
from mojodex_core.entities.instruct_task import InstructTask
from mojodex_core.entities.todo import Todo
from mojodex_core.llm_engine.mpt import MPT
from datetime import datetime, timedelta, timezone

class User(MdUser):

    @cached_property
    def available_instruct_tasks(self):
        try:
            session = object_session(self)
            return session.query(InstructTask). \
                join(MdUserTask, InstructTask.task_pk == MdUserTask.task_fk). \
                filter(MdUserTask.user_id == self.user_id). \
                filter(InstructTask.type == "instruct"). \
                filter(MdUserTask.enabled == True).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: available_tasks :: {e}")

    @cached_property
    def local_datetime(self):
        try:
            timestamp = datetime.now(timezone.utc)
            if self.timezone_offset:
                timestamp -= timedelta(minutes=self.timezone_offset)
            return timestamp
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: local_datetime :: {e}")

    @cached_property
    def datetime_context(self):
        try:
            return MPT("mojodex_core/instructions/user_datetime_context.mpt", weekday=self.local_datetime.strftime("%A"),
                   datetime=self.local_datetime.strftime("%d %B %Y"),
                   time=self.local_datetime.strftime("%H:%M")).prompt
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: datetime_context :: {e}")
        
    @cached_property
    def twenty_first_todo_list_items(self):
        """
        Returns the list of 20 first todos for the user along with their due dates
        """
        try:
            session = object_session(self)
            # Subquery to get the latest todo_scheduling for each todo
            latest_todo_scheduling = session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()
            # Get the current date in UTC
            now_utc = datetime.now(timezone.utc).date()
            results = session.query(MdTodo.description, latest_todo_scheduling.c.latest_scheduled_date) \
                .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                .filter(MdUser.user_id == self.user_id) \
                .filter(MdTodo.deleted_by_user.is_(None)) \
                .filter(MdTodo.completed.is_(None)) \
                .filter((latest_todo_scheduling.c.latest_scheduled_date - text(
                'md_user.timezone_offset * interval \'1 minute\'')) >= now_utc) \
                .order_by(latest_todo_scheduling.c.latest_scheduled_date.desc()) \
                .offset(0) \
                .limit(20) \
                .all()

            return [{'description': description, 'scheduled_date': scheduled_date} for description, scheduled_date in results]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: todo_list :: {e}")
        

    @cached_property
    def today_todo_list(self):
        """
        Returns the list of todos for the user that are scheduled for today
        """
        try:
            session = object_session(self)
            today = func.date_trunc('day', func.now())

            # Subquery to check if the last scheduled date is today
            last_scheduled_today = session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .filter(MdTodoScheduling.scheduled_date == today) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()
            
            return session.query(Todo) \
                .join(last_scheduled_today, last_scheduled_today.c.todo_fk == Todo.todo_pk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == Todo.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .filter(MdUserTask.user_id == self.user_id) \
                .filter(Todo.deleted_by_mojo.is_(None)) \
                .filter(Todo.deleted_by_user.is_(None)) \
                .filter(Todo.completed.is_(None)) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: today_todo_list :: {e}")
        

    # User's todo items that have been rescheduled today
    @cached_property
    def today_rescheduled_todo(self):
        """
        Returns the todo items that have been rescheduled today
        """
        try:
            today = func.date_trunc('day', func.now())
            session = object_session(self)
            return session.query(Todo) \
                .join(MdTodoScheduling, MdTodoScheduling.todo_fk == MdTodo.todo_pk) \
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == MdTodo.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .filter(MdUserTask.user_id == self.user_id) \
                .filter(
                    and_(
                        extract("day", MdTodoScheduling.creation_date) == extract("day", today),
                        extract("month", MdTodoScheduling.creation_date) == extract("month", today),
                        extract("year", MdTodoScheduling.creation_date) == extract("year", today),
                    )
                ) \
                .filter(MdTodoScheduling.reschedule_justification.isnot(None)) \
                .all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: today_rescheduled_todo :: {e}")
        


    def get_vocabulary(self, max_items=50):
        """
        Returns the user's vocabulary
        """
        try:
            session = object_session(self)
            return session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == self.user_id) \
                .order_by(MdUserVocabulary.creation_date.desc()).limit(max_items).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: vocabulary :: {e}")
        
    @cached_property
    def fifty_first_vocabulary_items(self):
        """
        Returns the first 50 vocabulary items for the user
        """
        try:
            return self.get_vocabulary(50)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: fifty_first_vocabulary :: {e}")