import { apiRoutes } from ".";
import {
  ExecuteTaskPayload,
  ExecuteTaskResponse,
  TaskConfigAPIResponse,
  TaskDonePayload,
  UserTaskExecution,
  UserTaskExecutionProducedTextResponse,
  UserTask,
  UserTasksAPIResponse,
  RestartWorkflowPayload,
  SaveResultPayload,
  SaveResultResponse,
  MessageHistoryResponse,
  SaveUserTaskExecutionTitleResponse,
  SaveUserTaskExecutionTitlePayload,
} from "modules/Tasks/interface";
import axiosClient from "./config/axiosClient";
import {
  TodoCompletePayload,
  TodosType,
} from "modules/Tasks/interface/todos";

export const getAllUserTasks = (): Promise<UserTasksAPIResponse> =>
  axiosClient.get(apiRoutes.userTasks);

export const getTask = ({ queryKey }: any): Promise<UserTask> =>
  axiosClient.get(apiRoutes.userTasks, {
    params: { user_task_pk: queryKey[1] },
  });

export const getTaskConfigs = ({
  queryKey,
}: any): Promise<TaskConfigAPIResponse> =>
  axiosClient.put(apiRoutes.taskConfigs, { user_task_pk: queryKey[1] });

function isFileArray(value: any): value is File[] {
  return Array.isArray(value) && value.every(item => item instanceof File);
}

const addUserInputsToForm = (userInputsFromForm: any[], formData: FormData) => {
  const json_inputs: any = [];
  userInputsFromForm.forEach((input: any) => {
    if ((input.input_value instanceof File)) {
      formData.append(input.input_name, input.input_value);
      json_inputs.push({
        "input_name": input.input_name,
        "input_value": input.input_value.name
      });
      
    }

    else {
      json_inputs.push({
        "input_name": input.input_name,
        "input_value": input.input_value.toString()
      });
    }
  });
  formData.append('inputs', JSON.stringify(json_inputs));
};

export const executeTask = (
  payload: ExecuteTaskPayload
): Promise<ExecuteTaskResponse> => {
  const formData = new FormData();
  (Object.keys(payload) as Array<keyof ExecuteTaskPayload>).forEach(key => {

    const value = payload[key];
    if (key == 'inputs') {
      addUserInputsToForm(payload['inputs'], formData);
    } else if (value !== undefined) {
      formData.append(key, value.toString());
    }
  });

  return axiosClient.post(apiRoutes.executeTask, formData);
}

export const onTaskComplete = (paylaod: TaskDonePayload) =>
  axiosClient.post(apiRoutes.taskConfigs, paylaod);

export const deleteUserTaskExecution = (userTaskExecutionPk: number) =>
  axiosClient.delete(apiRoutes.taskConfigs, {
    params: { user_task_execution_pk: userTaskExecutionPk },
  });

export const getUserTaskExecution = ({
  pageParam = 0,
  searchFilter,
  userTaskPks,
}: any): Promise<{
  user_task_executions: UserTaskExecution[];
}> =>
  axiosClient.get(apiRoutes.userTaskExecution, {
    params: {
      n_user_task_executions: pageParam == 0 ? 20 : 10,
      offset: pageParam,
      search_filter: searchFilter,
      user_task_pks: userTaskPks,
    },
  });

export const getExecuteTaskById = ({ queryKey }: any): Promise<UserTaskExecution> =>
  axiosClient.get(apiRoutes.userTaskExecution, {
    params: { user_task_execution_pk: queryKey[1] },
  });

export const getUserTaskExecutionProducedText = (producedTextIndex: number, userTaskExecutionPk: number): Promise<UserTaskExecutionProducedTextResponse> =>
  axiosClient.get(apiRoutes.userTaskExecutionProducedText, {
    params: {
      produced_text_version_index: producedTextIndex,
      user_task_execution_pk: userTaskExecutionPk,
    },
  });  //.then(response => response.data)


export const getMessageHistory = (
  sessionId: string
): Promise<MessageHistoryResponse> =>
  axiosClient.get(apiRoutes.messageHistory, {
    params: { session_id: sessionId },
  });

export const getAllTodos = ({
  pageParam = 0,
  nTodos = 50,
  queryKey,
}: any): Promise<TodosType> =>
  axiosClient.get(apiRoutes.todos, {
    params: {
      offset: pageParam,
      n_todos: nTodos,
      user_task_execution_fk: queryKey[1],
    },
  });

export const deleteTodo = (todoPk: number) =>
  axiosClient.delete(apiRoutes.todos, {
    params: { todo_pk: todoPk },
  });

export const onTodoComplete = (payload: TodoCompletePayload) =>
  axiosClient.post(apiRoutes.todos, payload);

export const validateUserTaskExecutionStepExecution = (stepExecutionPk: number) =>
  axiosClient.post(apiRoutes.userWorkflowStepExecution, {
    user_workflow_step_execution_pk: stepExecutionPk,
    validated: true
  });

export const invalidateUserTaskExecutionStepExecution = (stepExecutionPk: number) =>
  axiosClient.post(apiRoutes.userWorkflowStepExecution, {
    user_workflow_step_execution_pk: stepExecutionPk,
    validated: false
  });

export const relaunchStepExecution = (stepExecutionPk: number) =>
  axiosClient.put(apiRoutes.userWorkflowStepExecution, {
    user_workflow_step_execution_pk: stepExecutionPk,
  });

export const saveResultEdition = (payload: SaveResultPayload): Promise<SaveResultResponse> =>
  axiosClient.put(apiRoutes.userWorkflowStepExecutionResult, payload);

export const workflowRestart = (payload: RestartWorkflowPayload) => {
  const { user_task_execution_pk, inputs } = payload;
  const formData = new FormData();
  formData.append('user_task_execution_pk', user_task_execution_pk.toString());
  addUserInputsToForm(inputs, formData);
  return axiosClient.post(apiRoutes.workflowRestart, formData);
};

export const saveTaskExecutionTitle = (payload: SaveUserTaskExecutionTitlePayload): Promise<SaveUserTaskExecutionTitleResponse> =>
  axiosClient.post(apiRoutes.userTaskExecutionTitle, payload);