from mojodex_core.entities import MdUser
from mojodex_core.entities_controllers.entity_controller import EntityController


class User(EntityController):

    def __init__(self, user_id, db_session):
        super().__init__(MdUser, user_id, db_session)

    @property
    def user_id(self):
        try:
            return self.pk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: user_id :: {e}")

    @property
    def company_knowledge(self):
        try:
            return self.db_object.company_description
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: company_knowledge :: {e}")

    @property
    def username(self):
        try:
            return self.db_object.name
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: username :: {e}")

    @property
    def language_code(self):
        try:
            return self.db_object.language_code
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: language_code :: {e}")
