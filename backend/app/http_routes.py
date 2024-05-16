from routes.user import User
from routes.purchase import Purchase
from routes.company import Company
from routes.session import Session
from routes.error import Error
from routes.calendar_suggestion import CalendarSuggestion, CalendarSuggestionOldWelcomeMessage
from routes.terms_and_conditions import TermsAndConditions
from routes.onboarding import Onboarding
from routes.voice import Voice
from routes.user_message import UserMessage
from routes.produced_text import ProducedText
from routes.user_task import UserTask
from routes.user_task_execution import UserTaskExecution
from routes.user_task_execution_run import UserTaskExecutionRun
from routes.task import Task
from routes.user_summary import UserSummary
from routes.user_task_execution_summary import UserTaskExecutionSummary
from routes.password import Password
from routes.document import Document
from routes.document_chunk import DocumentChunk
from routes.message import Message
from routes.resource import MojoResource
from routes.goal import Goal
from routes.purchase_end_stripe_webhook import PurchaseEndStripeWebHook
from routes.check_expired_purchases import ExpiredPurchasesChecker
from routes.device import Device
from routes.daily_notifications import DailyNotifications
from routes.daily_emails import DailyEmails
from routes.event import Event
from routes.text_type import TextType
from routes.text_edit_action import TextEditAction
from routes.language import Language
from routes.timezone import Timezone
from routes.product import Product
from routes.product_task_association import ProductTaskAssociation
from routes.manual_purchase import ManualPurchase
from routes.task_tool_execution import TaskToolExecution
from routes.mojo_message import MojoMessage
from routes.inapp_apple_purchase import InAppApplePurchase
from routes.todos import Todos
from routes.extract_todos import ExtractTodos
from routes.todo_scheduling import TodosScheduling
from routes.todo_daily_emails import TodoDailyEmails
from routes.task_tool_query import TaskToolQuery
from routes.vocabulary import Vocabulary
from routes.product_category import ProductCategory
from routes.associate_free_product import FreeProductAssociation
from routes.free_users_engagement import FreeUsersEngagementChecker
from routes.retrieve_produced_text import RetrieveProducedText
from routes.calendar_suggestion_notification import CalendarSuggestionNotifications
from routes.home_chat import HomeChat
from routes.tool import Tool
from routes.task_tool import TaskTool
from routes.task_json import TaskJson
from routes.integrations.hubspot import Hubspot
from routes.user_workflow_step_execution import UserWorkflowStepExecution
from routes.user_task_execution_produced_text import UserTaskExecutionProducedText
from routes.profile_category import ProfileCategory
from routes.profile import Profile
from routes.role import Role
from routes.profile_task_association import ProfileTaskAssociation
from routes.image import Image
from routes.relaunch_locked_workflow_step_executions import RelaunchLockedWorkflowStepExecutions
from routes.is_email_service_configured import IsEmailServiceConfigured
from routes.user_workflow_step_execution_result import UserWorkflowStepExecutionResult
class HttpRouteManager:
    def __init__(self, api):
        api.add_resource(Purchase, '/purchase')
        api.add_resource(Session, '/session')
        api.add_resource(User, '/user')
        api.add_resource(Company, '/company')
        api.add_resource(Error, '/error')
        api.add_resource(CalendarSuggestion, '/calendar_suggestion')
        api.add_resource(CalendarSuggestionOldWelcomeMessage, '/welcome_message')
        api.add_resource(TermsAndConditions, '/terms_and_conditions')
        api.add_resource(Onboarding, '/onboarding')
        api.add_resource(Voice, '/voice')
        api.add_resource(UserMessage, '/user_message')
        api.add_resource(ProducedText, '/produced_text')
        api.add_resource(UserTask, '/user_task')
        api.add_resource(UserTaskExecution, '/user_task_execution')
        api.add_resource(UserTaskExecutionRun, '/user_task_execution_run')
        api.add_resource(Task, '/task')
        api.add_resource(UserSummary, '/user_summary')
        api.add_resource(UserTaskExecutionSummary, '/user_task_execution_summary')
        api.add_resource(Password, '/password')
        api.add_resource(Document, '/document')
        api.add_resource(DocumentChunk, '/document_chunk')
        api.add_resource(Message, "/message")
        api.add_resource(MojoResource, "/resource")
        api.add_resource(Goal, "/goal")
        api.add_resource(PurchaseEndStripeWebHook, "/subscription_end")
        api.add_resource(ExpiredPurchasesChecker, "/check_expired_purchases")
        api.add_resource(Device, "/device")
        api.add_resource(DailyNotifications, "/send_daily_notifications")
        api.add_resource(DailyEmails, "/send_daily_emails")
        api.add_resource(Event, "/event")
        api.add_resource(TextType, "/text_type")
        api.add_resource(TextEditAction, "/text_edit_action")
        api.add_resource(Language, "/language")
        api.add_resource(Timezone, "/timezone")
        api.add_resource(Product, "/product")
        api.add_resource(ProductTaskAssociation, "/product_task_association")
        api.add_resource(ManualPurchase, "/manual_purchase")
        api.add_resource(TaskToolExecution, "/task_tool_execution")
        api.add_resource(MojoMessage, "/mojo_message")
        api.add_resource(InAppApplePurchase, "/in_app_apple_purchase")
        api.add_resource(Todos, "/todos")
        api.add_resource(ExtractTodos, "/extract_todos")
        api.add_resource(TodosScheduling, "/todos_scheduling")
        api.add_resource(TodoDailyEmails, "/todo_daily_emails")
        api.add_resource(TaskToolQuery, "/task_tool_query")
        api.add_resource(Vocabulary, "/vocabulary")
        api.add_resource(ProductCategory, "/product_category")
        api.add_resource(FreeProductAssociation, "/associate_free_product")
        api.add_resource(FreeUsersEngagementChecker, "/check_disengaged_free_trial_users")
        api.add_resource(RetrieveProducedText, "/retrieve_produced_text")
        api.add_resource(CalendarSuggestionNotifications, "/calendar_suggestion_notifications")
        api.add_resource(HomeChat, "/home_chat")
        api.add_resource(Tool, "/tool")
        api.add_resource(TaskTool, "/task_tool")
        api.add_resource(TaskJson, "/task_json")
        api.add_resource(Hubspot, "/integrations/hubspot")
        api.add_resource(UserWorkflowStepExecution, "/user_workflow_step_execution")
        api.add_resource(UserTaskExecutionProducedText, "/user_task_execution_produced_text")
        api.add_resource(ProfileCategory, "/profile_category")
        api.add_resource(Profile, "/profile")
        api.add_resource(Role, "/role")
        api.add_resource(ProfileTaskAssociation, "/profile_task_association")
        api.add_resource(Image, "/image")
        api.add_resource(RelaunchLockedWorkflowStepExecutions, "/relaunch_locked_workflow_step_executions")
        api.add_resource(IsEmailServiceConfigured, "/is_email_service_configured")
        api.add_resource(UserWorkflowStepExecutionResult, "/user_workflow_step_execution_result")