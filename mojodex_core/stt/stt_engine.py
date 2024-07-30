from abc import ABC, abstractmethod


class SttEngine(ABC):

    @abstractmethod
    def transcribe(self, filepath, user_id, user_task_execution_pk, task_name_for_system):
        raise NotImplementedError("transcribe method is not implemented")


    @abstractmethod
    def transcribe_with_timestamp(self, filepath, user_id, user_task_execution_pk, task_name_for_system):
        raise NotImplementedError("transcribe_with_timestamp method is not implemented")