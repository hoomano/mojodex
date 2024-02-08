import { NewlyCreatedTaskInfo } from "modules/Tasks/interface";
import React, { createContext, useReducer } from "react";
import { SessionType } from "./interface/session";
import { Alert } from "components/Alerts";

export interface GlobalStateType {
  session?: SessionType | null;
  selectedDraftPk?: string | null;
  newlyCreatedTaskInfo?: NewlyCreatedTaskInfo | null;
  showTaskDoneModal?: boolean;
  alert?: Alert;
  mainChatInputRef?: HTMLTextAreaElement | null | undefined;
}

export interface GlobalContextType {
  globalState: GlobalStateType;
  setGlobalState: (payload: GlobalStateType) => void;
}

// Initial Values for the global context
const initialState = {
  session: null,
  selectedDraftPk: null,
  newlyCreatedTaskInfo: null,
  showTaskDoneModal: false,
  alert: {
    type: "primary",
    title: "",
    show: false,
  } as Alert,
};

// Context
const globalContext = createContext<GlobalContextType | GlobalStateType>(
  initialState
);

// Reducer
const reducer = (
  state: GlobalStateType,
  action: { type: string; payload: GlobalStateType }
) => {
  const { type, payload } = action;
  switch (type) {
    case "SET_STATE":
      return { ...state, ...payload };
    default:
      return state;
  }
};

// Provider
const GlobalContextProvider = ({ children }: { children: React.ReactNode }) => {
  const [globalState, dispatch] = useReducer(reducer, initialState);

  const setGlobalState = (payload: GlobalStateType) =>
    dispatch({
      type: "SET_STATE",
      payload,
    });

  const contextValues: GlobalContextType = {
    globalState,
    setGlobalState,
  };

  return (
    <globalContext.Provider value={contextValues}>
      {children}
    </globalContext.Provider>
  );
};

export { GlobalContextProvider };

export default globalContext;
