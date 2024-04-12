import { useMutation } from "@tanstack/react-query";
import { updateTaskMessageFormat } from "helpers/method";
import ChatContext from "modules/Chat/helpers/ChatContext";
import { ChatContextType, ChatStateType, ChatUsedFrom } from "modules/Chat/interface/context";
import { useContext, useEffect } from "react";
import { getMessageHistory } from "services/tasks";

const useGetMessageHistory = () => {
  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;

  const { sessionId, chatUsedFrom, isNewSession } = chatState;

  const msgHistory = useMutation(getMessageHistory);

  useEffect(() => {
    if (sessionId && !isNewSession) {
      msgHistory.mutate(sessionId, {
        onSuccess: (data) => {
          const formattedOldMessages = updateTaskMessageFormat(
            data.messages,
            chatUsedFrom || null
          );

          let buildChatState: ChatStateType = {
            messages: [...formattedOldMessages],
            inputDisabled: !formattedOldMessages.length && chatUsedFrom !== ChatUsedFrom.Workflow, // todo: only if current task is not a workflow
          };

          if (formattedOldMessages.length) {
            buildChatState.waitingForServer = false;
          }

          setChatState(buildChatState);
        },
      });
    }
  }, [sessionId, isNewSession]);
};

export default useGetMessageHistory;
