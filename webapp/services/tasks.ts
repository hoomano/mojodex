import { apiRoutes } from ".";
import {
  ExecuteTaskPayload,
  ExecuteTaskResponse,
  TaskConfigAPIResponse,
  TaskDonePayload,
  TaskType,
  UserTask,
  UserTasksAPIResponse,
} from "modules/Tasks/interface";
import axiosClient from "./config/axiosClient";
import {
  MessageHistoryResponse,
  TodoCompletePayload,
  TodosType,
} from "modules/Tasks/interface/action";

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

export const executeTask = (
  payload: ExecuteTaskPayload
): Promise<ExecuteTaskResponse> =>
  axiosClient.post(apiRoutes.executeTask, payload);

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
  user_task_executions: TaskType[];
}> =>
  axiosClient.get(apiRoutes.userTaskExecution, {
    params: {
      n_user_task_executions: pageParam == 0 ? 20 : 10,
      offset: pageParam,
      search_filter: searchFilter,
      user_task_pks: userTaskPks,
    },
  });

export const getExecuteTaskById = ({ queryKey }: any): Promise<TaskType> =>
  axiosClient.get(apiRoutes.userTaskExecution, {
    params: { user_task_execution_pk: queryKey[1] },
  });


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
