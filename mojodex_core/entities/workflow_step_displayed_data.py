from mojodex_core.entities.db_base_entities import MdWorkflowStepDisplayedData


class WorkflowStepDisplayedData(MdWorkflowStepDisplayedData):
    
    def to_json(self):
        try:
            return {
                "language_code": self.language_code,
                "name_for_user": self.name_for_user,
                "definition_for_user": self.definition_for_user
                }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")