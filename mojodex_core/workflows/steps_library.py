from mojodex_core.workflows.web_research_synthesis.search_sources import SearchSourcesStep
from mojodex_core.workflows.web_research_synthesis.write_synthesis_note import WriteSynthesisNoteStep
from mojodex_core.workflows.write_poem.divide_in_stanza import StanzaDividerStep
from mojodex_core.workflows.write_poem.write_stanza import StanzaWriterStep


steps_class = {
    "stanza_divider": StanzaDividerStep,
    "stanza_writer": StanzaWriterStep,
    "search_sources": SearchSourcesStep,
    "write_synthesis_note": WriteSynthesisNoteStep
}


