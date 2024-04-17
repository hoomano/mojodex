import { ChatUsedFrom } from "./context";

export interface MessageType {
  id?: string;
  session_id?: string;
  text?: string;
  from?: string;
  content?: string;
  type: string;
  produced_text?: string;
  question?: string;
  answer?: string;
  email?: string;
  subject?: string;
  message_pk?: string;
  source?: string;
  messageFor?: ChatUsedFrom;
  error?: string;
  produced_text_pk?: string;
  isMojoToken?: boolean;
  task_tool_execution_fk?: number;
  showTaskMessage?: boolean;
}

export interface ChatSession {
  session_id: string;
  title: string | null;
}

export interface GetChatHistoryResponse {
  sessions: ChatSession[];
}

export interface UserMessagePayload {
  session_id: string;
  message_id: string;
  message_date: string;
  text: string;
  user_task_execution_pk?: number;
  use_message_placeholder: boolean;
  use_draft_placeholder: boolean;
  origin: string;
}