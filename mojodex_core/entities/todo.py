from mojodex_core.entities.db_base_entities import MdTodo, MdTodoScheduling
from sqlalchemy.orm import object_session

class Todo(MdTodo):
    
    @property
    def n_times_scheduled(self):
        """
        Returns the number of times the todo has been scheduled
        """
        try:
            session = object_session(self)
            return session.query(MdTodoScheduling).filter(MdTodoScheduling.todo_fk == self.todo_pk).count()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: n_times_scheduled :: {e}")