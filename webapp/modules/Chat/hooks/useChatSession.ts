import { useMutation } from "@tanstack/react-query";
import { updateSession } from "services/general";
import { appPlatform } from "helpers/constants";
import { useContext } from "react";
import ChatContext from "../helpers/ChatContext";
import { ChatContextType } from "../interface/context";

const useChatSession = () => {
  const { setChatState } = useContext(ChatContext) as ChatContextType;

  return useMutation({
    mutationFn: () =>
      updateSession({
        datetime: new Date().toISOString(),
        platform: appPlatform,
      }),
    onSuccess: (data) => {
      setChatState({
        sessionId: data.session_id,
      });
    },
  });
};

export default useChatSession;
