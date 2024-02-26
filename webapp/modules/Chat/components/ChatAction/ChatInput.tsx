import React, { useState, useRef, useEffect, useContext } from "react";
import ChatSendButton from "./ChatSendButton";

import globalContext, { GlobalContextType } from "helpers/GlobalContext";

interface ChatInputType {
  prompt?: string;
  inputDisabled?: boolean;
  focusInput?: boolean;
  isMobile?: boolean;
  intro_done?: boolean;
  initial_msg?: boolean;
  textEdit: (text: string) => void;
  textEditEnd: () => void;
  onSend: (message?: string) => void;
}

const ChatInput = ({
  prompt,
  inputDisabled,
  focusInput,
  isMobile,
  intro_done,
  initial_msg,
  textEdit,
  textEditEnd,
  onSend,
}: ChatInputType) => {

  const [message, setMessage] = useState(prompt);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const { setGlobalState } = useContext(globalContext) as GlobalContextType;

  const placeholder = inputDisabled
    ? "Waiting for answer..."
    : "Write your message here...";

  // Focus the textarea when the component is mounted
  useEffect(() => {
    if (prompt) {
      setMessage(prompt);
      if (textareaRef.current) {
        // textareaRef.current.style.height = 'auto';
        // textareaRef.current.rows = textareaRef.current.scrollHeight;
        // textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height =
          textareaRef.current.scrollHeight + "px";
      }
    }
  }, [prompt]);

  // Handle the keydown event
  // If the user presses the Enter key, send the message
  // If the user presses the Shift + Enter keys, add a new line
  // If the user presses the Enter key on mobile, add a new line
  const handleKeyDown = (event: any) => {
    const textarea: any = event.target;

    if (event.key === "Enter" && event.shiftKey) {
      // do nothing, just return a new line in textarea
    } else if (event.key === "Enter" && !isMobile) {
      event.preventDefault();
      textEdit("");
      // Send the message
      sendMessage();
      textarea.style.height = "auto";
    } else if (event.key === "Enter" && isMobile) {
      // do nothing, just return a new line in textarea
    }
  };

  const sendMessage = () => {
    if (message === "") {
      return;
    }
    // Reset the state variable to an empty string
    setMessage("");
    onSend(message);
  };

  const handleInput = (event: any) => {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";

    // Update the state variable with the value entered by the user
    setMessage(event.target.value);
    if (event.target.value) {
      textEdit(event.target.value);
    } else {
      textEditEnd();
    }
  };

  const getPlaceholder = () => {
    if (inputDisabled || (!intro_done && !initial_msg)) {
      return "Wait a moment...";
    }
    return placeholder;
  };

  const isDisabled =
    inputDisabled || (!intro_done && !initial_msg);

  useEffect(() => {
    if (textareaRef.current && !isDisabled) {
      textareaRef.current?.focus();
      setGlobalState({ mainChatInputRef: textareaRef?.current });
    }
  }, [isDisabled]);

  // Render the component
  // The textarea is resized automatically when the user enters a new line
  return (
    <div className={`flex grow`}>
      <div className="w-1/12" />

      <form className="flex grow py-2 mb-1 items-end">
        

        <textarea
          ref={textareaRef}
          rows={1}
          placeholder={getPlaceholder()}
          className="flex-1 rounded-md px-4 ml-1 py-1 border-transparent focus:border-transparent focus:ring-0 text-white bg-gray-600 overflow-hidden"
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          style={{ resize: "none", height: "auto", width: "100%" }}
          value={message}
          disabled={isDisabled}
          autoFocus
        />
        <ChatSendButton onSend={sendMessage} enabled={!inputDisabled} />
      </form>
      <div className="w-1/12" />
    </div>
  );
};

export default ChatInput;
