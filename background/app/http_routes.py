from background.app.routes.create_document_from_website import CreateDocumentFromWebsite
from routes.update_document import UpdateDocument
from routes.event_generation import EventsGeneration
from routes.extract_todos import ExtractTodos
from routes.reschedule_todo import RescheduleTodo
class HttpRouteManager:
    def __init__(self, api):
        api.add_resource(CreateDocumentFromWebsite, '/create_document_from_website')
        api.add_resource(UpdateDocument, '/update_document')
        api.add_resource(EventsGeneration, '/events_generation')
        api.add_resource(ExtractTodos, '/extract_todos')
        api.add_resource(RescheduleTodo, '/reschedule_todo')