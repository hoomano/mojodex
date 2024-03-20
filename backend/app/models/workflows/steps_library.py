from models.workflows.write_poem.divide_in_stanza import StanzaDividerStep
from models.workflows.write_poem.write_stanza import StanzaWriterStep
from models.workflows.translation.section_translator import SectionsTranslatorStep
from models.workflows.translation.section_divier_step import SectionsDividerStep
from models.workflows.qualify_lead.query_writer_step import QueryWriterStep
from models.workflows.qualify_lead.search_step import SearchStep


steps_class = {
    "sections_translator": SectionsTranslatorStep,
    "section_divider": SectionsDividerStep,
    "query_writer": QueryWriterStep,
    "search": SearchStep,
    "stanza_divider": StanzaDividerStep,
    "stanza_writer": StanzaWriterStep
}