import { useContext } from "react";
import ChatContext from "modules/Chat/helpers/ChatContext";
import ChatMessages from "./ChatMessages";
import { useSession } from "next-auth/react";
import { ChatContextType } from "modules/Chat/interface/context";

const ChatBody = () => {
  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;
  const { data: session } = useSession();
  const profilePicture = session?.user?.image;

  const { isMobile, waitingForServer, messages } = chatState;

  return (
    <ChatMessages
      messages={messages}
      isMobile={isMobile}
      waitingForServer={waitingForServer}
      profilePicture={profilePicture}
    />
  );
};

export default ChatBody;
