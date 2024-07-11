from mojodex_core.workflows.write_poem.divide_in_stanza import StanzaDividerStep
from mojodex_core.workflows.write_poem.write_stanza import StanzaWriterStep
from mojodex_core.workflows.meeting_audio_recording_recap.transcribe_audio_recording import TranscribeAudioRecordingStep
from mojodex_core.workflows.meeting_audio_recording_recap.recap_meeting_transcription import RecapMeetingTranscriptionStep

steps_class = {
    "stanza_divider": StanzaDividerStep,
    "stanza_writer": StanzaWriterStep,
    "transcribe_audio_recording": TranscribeAudioRecordingStep,
    "recap_meeting_transcription": RecapMeetingTranscriptionStep
}


