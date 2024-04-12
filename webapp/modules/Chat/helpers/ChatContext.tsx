"use client";
import React, { createContext, useEffect, useReducer } from "react";
import {
  ChatContextType,
  ChatUsedFrom,
  ChatStateType,
} from "../interface/context";

// Initial Values for the context
const initialState = {
  messages: [], // used to store the messages
  sessionId: null, // used to identify the session
  waitingForServer: false, // waiting for a response from the server used to disable the input and show a spinner
  inputDisabled: false,
  focusInput: true, // used to focus the input when we receive a message from the agent and the user has to answer
  showSnackBar: false, // used to display a snackbar
  messageSnackBar: "", // used to store the message of the snackbar
  initialMsg: false,
  isMobile: false,
  prompt: "",
  socket: null,
  chatUsedFrom: ChatUsedFrom.Chat,
  currentTaskInfo: null,
  isNewSession: false,
};

// Context
const ChatContext = createContext<ChatContextType | ChatStateType>(
  initialState
);

// Reducer
const reducer = (
  state: ChatStateType,
  action: { type: string; payload: ChatStateType }
) => {
  const { type, payload } = action;
  switch (type) {
    case "SET_STATE":
      return { ...state, ...payload };
    default:
      return state;
  }
};

// If sessionId is falsy value then it will consider as fresh chat session
const ChatProvider = ({
  chatUsedFrom = ChatUsedFrom.Chat,
  children,
  sessionId,
}: {
  chatUsedFrom?: ChatUsedFrom;
  children: React.ReactNode;
    sessionId?: string | null | undefined;
}) => {
  const [chatState, dispatch] = useReducer(reducer, {
    ...initialState,
    chatUsedFrom
  });

  useEffect(() => {
    let payload: ChatStateType = {
      isNewSession: !sessionId,
      messages: [],
      initialMsg: false
    };

    // If we have old chat session, we'll bypass intro an initial notes
    if (sessionId) {
      payload = {
        ...payload,
        sessionId,
        initialMsg: true
      };
    }

    setChatState(payload);
  }, [sessionId]);

  const setChatState = (payload: ChatStateType) =>
    dispatch({
      type: "SET_STATE",
      payload,
    });

  const contextValues = {
    chatState,
    setChatState,
  };

  return (
    <ChatContext.Provider value={contextValues}>
      {children}
    </ChatContext.Provider>
  );
};

export { ChatProvider };

export default ChatContext;
