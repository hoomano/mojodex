export interface UserTask {
  user_task_pk?: number;
  task_pk: number;
  task_name: string;
  task_description: string;
  task_icon: string;
  enabled: boolean;
  task_type: string;
  steps:UserTaskStep[];
}

export interface UserTaskStep {
  workflow_step_pk: number;
  step_name_for_user: string;
  step_definition_for_user: string;
}

export interface UserTasksAPIResponse {
  user_tasks: UserTask[];
}

export interface TaskPreference {
  user_task_preference_pk: number;
  name: string;
  enabled?: boolean;
}

export interface TaskJsonInput {
  input_name: string;
  description_for_user: string;
  description_for_system: string;
  placeholder: string;
  type: string;
}

export interface TaskConfigAPIResponse {
  user_task_execution_pk: number;
  json_input: TaskJsonInput[];
  session_id: string;
  intro_done: boolean;
}

export interface InputArrayProps {
  input_name: string;
  input_value: string;
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

export interface TaskType {
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
  type: string;
  produced_text_pk: number;
  session_id: string;
  start_date: string;
  working_on_todos: boolean;
  n_todos: number;
  n_not_read_todos: number;
}

export interface EditerDraft {
  text: string;
  title: string;
  textPk: number | null;
}
