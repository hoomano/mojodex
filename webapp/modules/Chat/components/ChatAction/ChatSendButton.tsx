import React from "react";
import { FaPaperPlane } from "react-icons/fa"; // Import the send icon from the Font Awesome library

interface ChatSendButtonType {
  enabled: boolean;
  onSend: () => void;
}

const ChatSendButton = ({ enabled, onSend }: ChatSendButtonType) => {
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    //call onSend function prop when the button is clicked
    event.preventDefault();
    onSend();
  };

  if (enabled) {
    return (
      <button
        className="w-[38px] h-[38px] ml-2 rounded-full focus:outline-none focus:shadow-outline-gray bg-blue-600 hover:bg-blue-800 flex justify-center items-center"
        onClick={handleClick}
      >
        <FaPaperPlane className="w-5" color="#FFF" />
      </button>
    );
  } else {
    return <></>;
  }
};
export default ChatSendButton;
