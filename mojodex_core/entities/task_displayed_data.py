from mojodex_core.entities.db_base_entities import MdTaskDisplayedData


class TaskDisplayedData(MdTaskDisplayedData):
    
    def to_json(self):
        try:
            return {
                    "language_code": self.language_code,
                    "name_for_user": self.name_for_user,
                    "definition_for_user": self.definition_for_user,
                    "json_input": self.json_input
            } 
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")