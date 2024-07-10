from mojodex_core.entities.db_base_entities import MdPredefinedActionDisplayedData


class PredefinedActionDisplayedData(MdPredefinedActionDisplayedData):

    def to_json(self):
        try:
            return {"language_code": self.language_code,
                            "data": self.displayed_data}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")