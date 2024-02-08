import { useEffect, useContext } from "react";

import SnackBar from "components/Snackbar";


import ChatAction from "modules/Chat/components//ChatAction";
import ChatBody from "modules/Chat/components//ChatBody";


import useSocket from "./hooks/useSocket";

import ChatContext from "./helpers/ChatContext";
import { socketEvents } from "helpers/constants/socket";
import { ChatContextType, ChatUsedFrom } from "./interface/context";
import useGetMessageHistory from "modules/Tasks/hooks/useGetMessageHistory";
import useChatSession from "./hooks/useChatSession";

const Chat = () => {
  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;

  const {
    socket,
    sessionId,
    showSnackBar,
    messageSnackBar,
    chatUsedFrom,
    isNewSession,
  } = chatState;

  useSocket();
  useGetMessageHistory();

  const chatSession = useChatSession();

  useEffect(() => {
    if (isNewSession) chatSession.mutate();
  }, [isNewSession]);

  useEffect(() => {
    setChatState({
      isMobile:
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          navigator.userAgent
        ),
    });
  }, []);


  return (
    <div className="flex flex-col bg-gray-800 supports-[height:100cqh]:h-[100cqh] supports-[height:100svh]:h-[100svh]">


      <ChatBody />
      <div className="flex px-4 bg-gray-800">
        <ChatAction />
      </div>

      {showSnackBar && <SnackBar message={messageSnackBar} />}
    </div>
  );
};

export default Chat;
