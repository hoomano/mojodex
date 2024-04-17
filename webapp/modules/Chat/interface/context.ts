

export enum ChatUsedFrom {
  Chat = "Chat",
  Task = "Task",
  Workflow = "Workflow"
}

export interface ChatStateType {
  messages?: any;
  sessionId?: string | null;
  waitingForServer?: boolean;
  inputDisabled?: boolean;
  focusInput?: boolean;
  showSnackBar?: boolean;
  messageSnackBar?: string;
  initialMsg?: boolean;
  isMobile?: boolean;
  prompt?: string;
  socket?: any;
  chatUsedFrom?: ChatUsedFrom;
  currentTaskInfo?: {
    producedTextPk: number | null;
    taskExecutionPK: number;
  } | null;
  isNewSession?: boolean;
}

export interface ChatContextType {
  chatState: ChatStateType;
  setChatState: (payload: ChatStateType) => void;
}
