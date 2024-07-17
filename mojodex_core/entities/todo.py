from functools import cached_property
from mojodex_core.entities.db_base_entities import MdTodo, MdTodoScheduling
from sqlalchemy.orm import object_session
from datetime import date

class Todo(MdTodo):
    
    @cached_property
    def n_times_scheduled(self):
        """
        Returns the number of times the todo has been scheduled
        """
        try:
            session = object_session(self)
            return session.query(MdTodoScheduling).filter(MdTodoScheduling.todo_fk == self.todo_pk).count()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: n_times_scheduled :: {e}")
        
    @cached_property
    def scheduling(self) -> MdTodoScheduling:
        """
        Returns the last todo_scheduling for the todo
        """
        try:
            session = object_session(self)
            return session.query(MdTodoScheduling) \
                .filter(MdTodoScheduling.todo_fk == self.todo_pk) \
                .order_by(MdTodoScheduling.scheduled_date.desc()) \
                .first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: scheduled_date :: {e}")
        
    @cached_property
    def scheduled_date(self) -> date:
        """
        Returns the date the todo is scheduled for
        """
        try:
            return self.scheduling.scheduled_date
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: schedule_date :: {e}")
        
        
