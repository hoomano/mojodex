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
  tool_execution_fk?: number;
  showTaskMessage?: boolean;
}

export interface ChatSession {
  session_id: string;
  title: string | null;
}

export interface GetChatHistoryResponse {
  sessions: ChatSession[];
}
