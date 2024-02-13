from routes.user_task_execution_title_and_summary import UserTaskExecutionTitleAndSummary
from routes.parse_website import ParseWebsite
from routes.update_document import UpdateDocument
from routes.first_session_message import FirstSessionMessage
from routes.event_generation import EventsGeneration
from routes.task_tool_execution import TaskToolExecution
from routes.extract_todos import ExtractTodos
from routes.reschedule_todo import RescheduleTodo
from routes.update_user_preferences import UpdateUserPreferences
class HttpRouteManager:
    def __init__(self, api):
        api.add_resource(UserTaskExecutionTitleAndSummary, '/user_task_execution_title_and_summary')
        api.add_resource(ParseWebsite, '/parse_website')
        api.add_resource(UpdateDocument, '/update_document')
        api.add_resource(FirstSessionMessage, '/first_session_message')
        api.add_resource(EventsGeneration, '/events_generation')
        api.add_resource(TaskToolExecution, '/task_tool_execution')
        api.add_resource(ExtractTodos, '/extract_todos')
        api.add_resource(RescheduleTodo, '/reschedule_todo')
        api.add_resource(UpdateUserPreferences, '/update_user_preferences')