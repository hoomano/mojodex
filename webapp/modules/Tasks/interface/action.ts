import { MessageType } from "modules/Chat/interface";


export interface MessageHistoryResponse {
  messages: { sender: string; message: MessageType }[];
}

export interface TodosType {
  todos: Todos[];
  user_has_never_done_todo: boolean;
  n_todos_not_read: number;
}

export interface Todos {
  todo_pk: number;
  user_task_execution_fk: number;
  description: string;
  scheduled_date: string;
  completed: string;
  creation_date: string;
  read_by_user: boolean;
}

export interface TodoCompletePayload {
  datetime: string;
  mark_as_read?: boolean;
  mark_as_done: boolean;
  todo_pk?: number;
  user_task_execution_pk?: number;
}
