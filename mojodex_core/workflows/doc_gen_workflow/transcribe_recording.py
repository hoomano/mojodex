
from typing import List
from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.stt.stt_service import STTService
from mojodex_core.user_storage_manager.user_video_file_manager import UserVideoFileManager

class TranscribeRecordingStep(WorkflowStep):
    

    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameters: dict,
                 past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int,
                 task_name_for_system: str, session_id: str):
        try:
            """ This step includes:
            1. Loading the recording from the filestorage
            2. Transcribing the content of the recording
            3. Dividing the transcription into chapters
            4. Returning the chapters as a list of strings including the timestamp of the beginning of each chapter in seconds from the start.
            """
            
            recording_filepath = UserVideoFileManager().get_video_file_from_form_storage_path(initial_parameters['video_recording'], user_id, session_id)

            # Transcribe the audio from STT
            transcription_list = STTService().transcribe_with_timestamp(recording_filepath, user_id, user_task_execution_pk, task_name_for_system)
            transcription = ""
            
            for t in transcription_list:
                transcription += str(t.start_time.seconds) + " --> " + str(t.end_time.seconds) + ": " + t.text + "\n"

            return [{'transcription': transcription}]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _execute: {e}")