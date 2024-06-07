from mojodex_core.entities import MdTask, MdTaskDisplayedData
from sqlalchemy import func, or_


class InstructTask:

    def __init__(self, task_pk, db_session):
        self.task_pk = task_pk
        self.db_session = db_session
        self.db_object = self._get_db_object(task_pk)

    def _get_db_object(self, task_pk):
        try:
            return self.db_session.query(MdTask).filter(MdTask.task_pk == task_pk).first()
        except Exception as e:
            raise Exception(f"_get_db_object :: {e}")

    @property
    def infos_to_extract(self):
        try:
            return self.db_object.infos_to_extract
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: infos_to_extract :: {e}")

    @property
    def name_for_system(self):
        try:
            return self.db_object.name_for_system
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: name_for_system :: {e}")

    @property
    def definition_for_system(self):
        try:
            return self.db_object.definition_for_system
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: description :: {e}")

    @property
    def icon(self):
        try:
            return self.db_object.icon
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: icon :: {e}")

    @property
    def output_format_instruction_title(self):
        try:
            return self.db_object.output_format_instruction_title
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_title :: {e}")

    @property
    def output_format_instruction_draft(self):
        try:
            return self.db_object.output_format_instruction_draft
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_format_instruction_draft :: {e}")

    @property
    def final_instruction(self):
        try:
            return self.db_object.final_instruction
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: final_instruction :: {e}")

    @property
    def output_text_type_fk(self):
        try:
            return self.db_object.output_text_type_fk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: output_text_type_fk :: {e}")

    def _get_displayed_data_in_language(self, language_code):
        try:
            return self.db_session.query(MdTaskDisplayedData).filter(MdTaskDisplayedData.task_fk == self.task_pk) \
                .filter(
                or_(
                    MdTaskDisplayedData.language_code == language_code,
                    MdTaskDisplayedData.language_code == 'en'
                )
            ).order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
            ).first()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _get_displayed_data_in_language :: {e}")

    def get_name_in_language(self, language_code):
        try:
            return self._get_displayed_data_in_language(language_code).name_for_user
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_name_in_language :: {e}")

    def get_json_input_in_language(self, language_code):
        try:
            return self._get_displayed_data_in_language(language_code).json_input
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_json_input_in_language :: {e}")
