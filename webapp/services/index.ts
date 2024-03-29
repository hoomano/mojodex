const generalAPIRoutes = {
  updateSession: "api/session",
  acceptTermsAndCondition: "api/terms_and_conditions",
  createDraft: "api/produced_text",
  language: "api/language",
  timezone: "api/timezone",
};

const taskAPIRoutes = {
  userTasks: "/api/user_task",
  taskConfigs: "/api/user_task_execution",
  executeTask: "/api/user_task_execution_run",
  userTaskExecution: "/api/task/user_task_execution",
  messageHistory: "/api/task/message",
  todos: "/api/todos",
};

const draftAPIRoutes = {
  deleteDraft: "/api/produced_text",
  saveDraft: "/api/produced_text",
  drafts: "/api/produced_text",
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

const chatHistoryAPIRoutes = {
  chatHistory: "api/session",
  editChat: "api/session",
  deleteChat: "api/session",
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

const taskToolExecutionsAPIRoutes = {
  acceptTaskToolExecution: "/api/task_tool_execution"
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
  ...draftAPIRoutes,

  // Chat History API's
  ...chatHistoryAPIRoutes,

  // resource API's
  ...resourcesAPIRoutes,

  ...paymentAPIRoutes,

  ...taskToolExecutionsAPIRoutes,
};
