import React, { useRef, useState } from "react";
import Image from "next/image";
import { FaTimes, FaCopy, FaCheck } from "react-icons/fa";
import ToolTip from "components/Tooltip";
import { EnvelopeIcon } from "@heroicons/react/20/solid";
import ShareableDraft from "components/ShareableDraft";
import { MessageType } from "modules/Chat/interface";
import {
  CheckCircleIcon,
  LinkIcon,
  XCircleIcon,
} from "@heroicons/react/24/solid";

interface ChatMessageType {
  sender?: string;
  message: MessageType;
  isMobile?: boolean;
  profilePicture?: string | null;
}

const ChatMessage = ({
  sender,
  message,
  isMobile,
  profilePicture,
}: ChatMessageType) => {
  let content = null;
  switch (message.type) {
    case "message":
      content = <Message message={message} />;
      break;
    case "mojo_message":
      if (message.produced_text !== undefined) {
        content = <ShareableDraft message={message} isMobile={isMobile} />;
      } else {
        content = <MojoMessage message={message} isMobile={isMobile} />;
      }
      break;
    case "text":
      content = <Text message={message} isMobile={isMobile} />;
      break;

    case "waitingForServer":
      content = <WaitingForServer />;
      break;

    default:
      break;
  }

  const ProfilePicture = () => {
    if (sender == "user") {
      if (profilePicture) {
        return <img src={profilePicture} alt=" " />;
      }
      return (
        <Image
          priority
          src="/images/default_user.png"
          className="object-cover w-8 h-8 items-center"
          height={144}
          width={144}
          alt=""
        />
      );
    } else {
      return (
        <Image
          priority
          src="/images/logo/mojodex_logo.png"
          className="object-cover w-8 h-8 items-center"
          height={144}
          width={144}
          alt=""
        />
      );
    }
  };

  return (
    <div
      id={`message-id-${message.id}`} // Used to scroll to bottom of the chat
      className={`flex items-start p-4 ${sender === "user" ? "bg-gray-600" : "bg-gray-700"
        }`}
    >
      <div className="  w-8 h-8 rounded-md flex-shrink-0 overflow-hidden">
        <ProfilePicture />
      </div>
      <div className="flex flex-grow ml-4 ">{content}</div>
    </div>
  );
};

export default ChatMessage;

const Message = ({ message }: { message: MessageType }) => {
  /// Manage \n for multilines
  const lines = message?.content?.split("\n") || [];
  const properNounRegex = /\*(.*?)\*/g;
  const messageWithBreaks = lines.map((line, index) => {
    return (
      <span key={index}>
        {line?.replace(properNounRegex, "$1")}
        <br />
      </span>
    );
  });

  return (
    <div className="mt-1 text-sm text-white">
      <p>{messageWithBreaks}</p>
    </div>
  );
};

const WaitingForServer = () => {
  return (
    <div className="flex flex-row items-center mt-1 text-sm text-gray-500 italic">
      <p></p>
      <div className="flex flex-row ml-4 items-center">
        <div className="dot-flashing"></div>
      </div>
    </div>
  );
};

const MojoMessage = ({ message }: ChatMessageType) => {
  /// Manage \n for multilines
  const lines = message?.question ? message?.question.split("\n") : [];
  const messageWithBreaks = lines.map((line, index) => {
    return (
      <span key={index}>
        {line}
        <br />
      </span>
    );
  });

  return (
    <div className="flex flex-grow flex-row justify-between">
      <div className="flex flex-col flex-grow mt-1 text-sm text-white">
        <div className="mt-1 text-sm text-white">
          <p>{messageWithBreaks}</p>
        </div>
      </div>
    </div>
  );
};


const Text = ({ message }: ChatMessageType) => {
  const textToCopy = useRef(null);

  /// Manage \n for multilines
  const lines = message?.content?.split("\n") || [];
  const textWithBreaks = lines.map((line, index) => {
    return (
      <span key={index}>
        {line}
        <br />
      </span>
    );
  });

  return (
    <div className="flex flex-grow flex-row justify-between">
      <div className="flex flex-col flex-grow mt-1 text-sm text-white">
        <p ref={textToCopy} className="mt-2">
          {textWithBreaks}
        </p>
      </div>
    </div>
  );
};

export const TaskMessage = ({ message }: ChatMessageType) => (
  <div className="text-sm">
    <div className="rounded-lg border overflow-hidden bg-gray-light text-black">
      <div className="p-[10px] bg-gray-light">
        <div className="pb-1.5 font-medium">{message.question}</div>

        <div className="flex gap-2 items-center">
          {message.answer ? (
            <>
              <CheckCircleIcon className="w-4 text-success-primary" /> Answer
              found
            </>
          ) : (
            <>
              <XCircleIcon className="w-4 text-error" />
              Answer missing
            </>
          )}
        </div>
      </div>

      {message?.answer && (
        <div className="bg-white p-[10px]">{message.answer}</div>
      )}
    </div>

    {message?.source && (
      <div className="pt-[10px] grid grid-cols-[30px_1fr] items-center text-gray-light">
        <LinkIcon className="w-4" />
        <a className="text-white" href={message.source} target="_blank">
          {message.source}
        </a>
      </div>
    )}
  </div>
);
