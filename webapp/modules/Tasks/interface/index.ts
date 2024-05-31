import { MessageType } from "modules/Chat/interface";

export interface MessageHistoryResponse {
  messages: { sender: string; message: MessageType }[];
}

export interface UserTask {
  user_task_pk?: number;
  task_pk: number;
  task_name: string;
  task_description: string;
  task_icon: string;
  enabled: boolean;
  task_type: string;
}


export interface UserTaskExecutionStepExecution {
  workflow_step_pk: number;
  step_name_for_user: string;
  step_definition_for_user: string;
  creation_date: string;
  user_workflow_step_execution_pk: number;
  user_validation_required: boolean;
  validated: boolean;
  parameter: any;
  result: Array<Map<string, any>>;
  error_status: any;
}

export interface UserTasksAPIResponse {
  user_tasks: UserTask[];
}

export interface TaskPreference {
  user_task_preference_pk: number;
  name: string;
  enabled?: boolean;
}

export interface TaskJsonInputPossibleValues {
  value: string;
  displayed_text: string;
}

export interface TaskJsonInput {
  input_name: string;
  description_for_user: string;
  description_for_system: string;
  placeholder: string;
  type: string;
  value: string | undefined;
  possible_values: TaskJsonInputPossibleValues[] | undefined;
}

export interface TaskConfigAPIResponse {
  user_task_execution_pk: number;
  json_input: TaskJsonInput[];
  session_id: string;
  intro_done: boolean;
}

export interface InputArrayProps {
  input_name: string;
  input_value: string | File;
}

export interface NewlyCreatedTaskInfo {
  taskExecutionPK: number;
  sessionId: string;
  inputArray: InputArrayProps[];
  taskType: string;
}

export interface ExecuteTaskPayload {
  datetime: string;
  user_task_execution_pk: number;
  inputs: InputArrayProps[];
}

export interface ExecuteTaskResponse {
  produced_text: string;
  produced_text_pk: number;
  produced_text_title: string;
}

export interface TaskDonePayload {
  datetime: string;
  user_task_execution_pk: number;
}

export interface UserTaskExecution {
  end_date: string;
  n_processes: number;
  summary: string;
  title: string;
  user_task_execution_pk: number;
  icon: string;
  user_task_pk: number;
  produced_text_title: string;
  produced_text_production: string;
  task_name: string;
  task_type: string;
  produced_text_pk: number;
  produced_text_version_pk: number;
  produced_text_version_index: number;
  session_id: string;
  json_inputs_values: TaskJsonInput[];
  start_date: string;
  working_on_todos: boolean;
  n_todos: number;
  n_not_read_todos: number;
  steps: any;
  step_executions: UserTaskExecutionStepExecution[];
}

export interface UserTaskExecutionProducedTextResponse {
  produced_text_production: string;
  produced_text_title: string;
  produced_text_version_index: number;
  produced_text_pk: number;
  produced_text_version_pk: number;
}

export interface EditerProducedText {
  text: string;
  title: string;
  producedTextPk: number | null;
}

export interface SaveResultPayload {
  user_workflow_step_execution_pk: number;
  result: Array<{ [k: string]: string; }>;
}

export interface SaveResultResponse {
  new_result: Array<Map<string, string>>;
}

export interface RestartWorkflowPayload{
  user_task_execution_pk: number;
  inputs: InputArrayProps[];
}