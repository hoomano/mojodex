import { send } from "process";

const generalAPIRoutes = {
  updateSession: "api/session",
  acceptTermsAndCondition: "api/terms_and_conditions",
  createDraft: "api/produced_text",
  language: "api/language",
  timezone: "api/timezone",
  isEmailServiceConfigured: "api/is_email_service_configured"
};

const taskAPIRoutes = {
  userTasks: "/api/user_task",
  taskConfigs: "/api/user_task_execution",
  executeTask: "/api/multiformdata/user_task_execution_run",
  userTaskExecution: "/api/task/user_task_execution",
  userTaskExecutionProducedText: "/api/task/user_task_execution_produced_text",
  messageHistory: "/api/task/message",
  todos: "/api/todos",
  userWorkflowStepExecution: "/api/user_workflow_step_execution",
  userWorkflowStepExecutionResult: "/api/user_workflow_step_execution_result",
  workflowRestart: "/api/restart_user_workflow_execution"
};

const producedTextAPIRoutes = {
  deleteProducedText: "/api/produced_text",
  saveProducedText: "/api/produced_text",
  producedText: "/api/produced_text",
};

const authAPIRoutes = {
  forgotPassword: "/api/user/password",
  resetPassword: "/api/user/password",
};

const onboardingAPIRoutes = {
  registerCompany: "/api/company",
  updateCompanyDetails: "/api/company",
  goal: "api/goal",
  productCategories: "api/product_category",
  updateProductCategory: "api/associate_free_product",
  onboardingPresented: "api/onboarding"
};

const chatAPIRoutes = {
  chatHistory: "api/session",
  editChat: "api/session",
  deleteChat: "api/session",
  sendUserMessage: "api/user_message",
};

const resourcesAPIRoutes = {
  getResources: "/api/resource",
  deleteResource: "/api/resource",
  addDocument: "/api/resource",
  refreshDocument: "/api/resource",
};

const paymentAPIRoutes = {
  createStripeCheckoutSession: "/api/stripe/create-session",
  purchaseStatus: "/api/purchase",
};


export const apiRoutes = {
  // Auth API's
  ...authAPIRoutes,

  // Onboarding API's
  ...onboardingAPIRoutes,

  // General API's
  ...generalAPIRoutes,

  // Task API's
  ...taskAPIRoutes,

  // Draft API's
  ...producedTextAPIRoutes,

  // Chat History API's
  ...chatAPIRoutes,

  // resource API's
  ...resourcesAPIRoutes,

  ...paymentAPIRoutes
};
