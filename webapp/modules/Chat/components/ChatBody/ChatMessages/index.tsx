import React from "react";
import ChatMessage from "./ChatMessage";
import { MessageType } from "modules/Chat/interface";

interface MessagesType {
  messages: MessageType[];
  waitingForServer?: boolean;
  isMobile?: boolean;
  profilePicture?: string | null;
}

const Messages = ({
  messages,
  waitingForServer,
  isMobile,
  profilePicture,
}: MessagesType) => {
  const list_messages = [];
  // Render the list of messages
  if (messages.length != 0) {
    messages.forEach((element) => {
      list_messages.push(
        <ChatMessage
          key={element.id}
          sender={element.from}
          message={element}
          isMobile={isMobile}
          profilePicture={profilePicture}
        />
      );
    });
  }

  // Render the waiting for server message
  if (waitingForServer) {
    list_messages.push(
      <ChatMessage
        key="waitingForServer"
        sender="server"
        message={{
          type: "waitingForServer",
        }}
      />
    );
  }

  return (
    <div className="mojodex-extension h-full w-full flex bg-gray-800 flex-col-reverse overflow-y-scroll scrollbar-hide">
      {list_messages.reverse()}
    </div>
  );
};

export default Messages;
