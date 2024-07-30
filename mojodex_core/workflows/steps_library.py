from mojodex_core.workflows.web_research_synthesis.search_sources import SearchSourcesStep
from mojodex_core.workflows.web_research_synthesis.write_synthesis_note import WriteSynthesisNoteStep
from mojodex_core.workflows.write_poem.divide_in_stanza import StanzaDividerStep
from mojodex_core.workflows.write_poem.write_stanza import StanzaWriterStep
from mojodex_core.workflows.doc_gen_workflow.chapters_to_doc import ChaptersToDocStep
from mojodex_core.workflows.doc_gen_workflow.transcription_to_chapters import TranscriptionToChaptersStep
from mojodex_core.workflows.doc_gen_workflow.transcribe_recording import TranscribeRecordingStep

steps_class = {
    "stanza_divider": StanzaDividerStep,
    "stanza_writer": StanzaWriterStep,
    "search_sources": SearchSourcesStep,
    "write_synthesis_note": WriteSynthesisNoteStep,
    "transcribe_recording": TranscribeRecordingStep,
    "transcription_to_chapters": TranscriptionToChaptersStep,
    "chapters_to_doc": ChaptersToDocStep,
}


