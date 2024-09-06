from routes.user import User
from routes.purchase import Purchase
from routes.company import Company
from routes.session import Session
from routes.error import Error
from routes.terms_and_conditions import TermsAndConditions
from routes.onboarding import Onboarding
from routes.voice import Voice
from routes.user_message import UserMessage
from routes.produced_text import ProducedText
from routes.user_task import UserTask
from routes.user_task_execution import UserTaskExecution
from routes.user_task_execution_run import UserTaskExecutionRun
from routes.task import Task
from routes.user_task_execution_title import UserTaskExecutionTitle
from routes.password import Password
from routes.message import Message
from routes.resource import MojoResource
from routes.goal import Goal
from routes.purchase_end_stripe_webhook import PurchaseEndStripeWebHook
from routes.check_expired_purchases import ExpiredPurchasesChecker
from routes.device import Device
from routes.text_type import TextType
from routes.text_edit_action import TextEditAction
from routes.language import Language
from routes.timezone import Timezone
from routes.product import Product
from routes.product_task_association import ProductTaskAssociation
from routes.manual_purchase import ManualPurchase
from routes.todos import Todos
from routes.vocabulary import Vocabulary
from routes.product_category import ProductCategory
from routes.associate_free_product import FreeProductAssociation
from routes.free_users_engagement import FreeUsersEngagementChecker
from routes.home_chat import HomeChat
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
from routes.is_push_notif_service_configured import IsPushNotifServiceConfigured
from routes.user_workflow_step_execution_result import UserWorkflowStepExecutionResult
from routes.restart_user_workflow_execution import RestartUserWorkflowExecution
from routes.statistics import Statistics

class HttpRouteManager:
    def __init__(self, api):
        api.add_resource(Purchase, '/purchase')
        api.add_resource(Session, '/session')
        api.add_resource(User, '/user')
        api.add_resource(Company, '/company')
        api.add_resource(Error, '/error')
        api.add_resource(TermsAndConditions, '/terms_and_conditions')
        api.add_resource(Onboarding, '/onboarding')
        api.add_resource(Voice, '/voice')
        api.add_resource(UserMessage, '/user_message')
        api.add_resource(ProducedText, '/produced_text')
        api.add_resource(UserTask, '/user_task')
        api.add_resource(UserTaskExecution, '/user_task_execution')
        api.add_resource(UserTaskExecutionRun, '/user_task_execution_run')
        api.add_resource(Task, '/task')
        api.add_resource(UserTaskExecutionTitle, '/user_task_execution_title')
        api.add_resource(Password, '/password')
        api.add_resource(Message, "/message")
        api.add_resource(MojoResource, "/resource")
        api.add_resource(Goal, "/goal")
        api.add_resource(PurchaseEndStripeWebHook, "/subscription_end")
        api.add_resource(ExpiredPurchasesChecker, "/check_expired_purchases")
        api.add_resource(Device, "/device")
        api.add_resource(TextType, "/text_type")
        api.add_resource(TextEditAction, "/text_edit_action")
        api.add_resource(Language, "/language")
        api.add_resource(Timezone, "/timezone")
        api.add_resource(Product, "/product")
        api.add_resource(ProductTaskAssociation, "/product_task_association")
        api.add_resource(ManualPurchase, "/manual_purchase")
        api.add_resource(Todos, "/todos")
        api.add_resource(Vocabulary, "/vocabulary")
        api.add_resource(ProductCategory, "/product_category")
        api.add_resource(FreeProductAssociation, "/associate_free_product")
        api.add_resource(FreeUsersEngagementChecker, "/check_disengaged_free_trial_users")
        api.add_resource(HomeChat, "/home_chat")
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
        api.add_resource(IsPushNotifServiceConfigured, "/is_push_notif_service_configured")
        api.add_resource(UserWorkflowStepExecutionResult, "/user_workflow_step_execution_result")
        api.add_resource(RestartUserWorkflowExecution, "/restart_user_workflow_execution")
        api.add_resource(Statistics, '/statistics')