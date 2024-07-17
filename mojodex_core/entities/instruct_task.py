from mojodex_core.entities.task import Task


class InstructTask(Task):

      def to_json(self):
        try:
            return {
                **super().to_json(),
                "final_instruction": self.final_instruction,
                "output_format_instruction_title": self.output_format_instruction_title,
                "output_format_instruction_draft": self.output_format_instruction_draft,
                "infos_to_extract": self.infos_to_extract,
                }
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: to_json :: {e}")


