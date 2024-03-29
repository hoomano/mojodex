

export enum ChatUsedFrom {
  Chat = "Chat",
  Task = "Task",
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
    text: string;
    title: string;
    textPk: number | null;
    taskExecutionPK: number;
  } | null;
  isNewSession?: boolean;
}

export interface ChatContextType {
  chatState: ChatStateType;
  setChatState: (payload: ChatStateType) => void;
}
