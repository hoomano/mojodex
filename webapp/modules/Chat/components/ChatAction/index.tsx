import { useContext, useState } from "react";

import ChatContext from "modules/Chat/helpers/ChatContext";

import ChatInput from "./ChatInput";
import ChatAcceptToolButtons from "./ChatAcceptToolButtons";

import { appVersion, appPlatform } from "helpers/constants";
import { socketEvents } from "helpers/constants/socket";
import useContextSession from "helpers/hooks/useContextSession";
import { ChatContextType, ChatUsedFrom } from "modules/Chat/interface/context";
import useApproveTaskToolExecution from "modules/TaskToolExecution/hooks/useApproveTaskToolExecution";
import useSendUserMessage from "modules/Chat/hooks/useSendUserMessage";
import { UserMessagePayload } from "modules/Chat/interface";

const scrollToLastMsg = (messageId: string) => {
  document.getElementById(`message-id-${messageId}`)?.scrollIntoView({
    behavior: "smooth",
  });
};

const ChatAction = ({ showPopup }: { showPopup: () => void }) => {
  const session = useContextSession();

  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;
  
  const userLanguage = session?.authorization?.language_code;
  const sendTaskToolExecutionApproval = useApproveTaskToolExecution();
  const sendUserMessage = useSendUserMessage();

  const {
    isMobile,
    prompt,
    inputDisabled,
    focusInput,
    initialMsg,
    messages,
    socket,
    sessionId,
  } = chatState;

  const sendMessage = (message?: string) => {
    if (!message) {
      return;
    }
    textEditEnd();
    let allMessages = messages;
    const currentMessageId = messages.length;

    const newMessage = {
      id: currentMessageId,
      from: "user",
      content: message,
      type: "message",
    };
    allMessages = [...allMessages, newMessage];


    function toISOStringLocal(date: Date) {
      const offsetMs = date.getTimezoneOffset() * 60 * 1000;
      const msLocal = date.getTime() - offsetMs;
      const dateLocal = new Date(msLocal);
      const iso = dateLocal.toISOString();
      const isoLocal = iso.slice(0, 19);
      return isoLocal;
    }

    // Send the message to the server
    if (socket) {
      const currentDatetime: Date = new Date();
      const isoString: string = toISOStringLocal(currentDatetime);
      const timezoneOffsetMinutes: string = currentDatetime.getTimezoneOffset().toString();
      let payload: UserMessagePayload = {
        text: message,
        session_id: sessionId!,
        //version: appVersion,
        //platform: appPlatform,
        message_id: `${isoString}_${sessionId}`,
        message_date: isoString,
        use_message_placeholder: false,
        use_draft_placeholder: false,
        origin: chatState.currentTaskInfo?.taskExecutionPK ? "task" : "home_chat",
      };

      if (chatState.currentTaskInfo?.taskExecutionPK) {
        const { taskExecutionPK, text, textPk, title } =
          chatState.currentTaskInfo;

        payload = {
          ...payload,
          //displayed_workspace: true,
          //displayed_workspace_draft: text,
          //displayed_workspace_title: title,
          //displayed_workspace_produced_text_pk: textPk,
          user_task_execution_pk: taskExecutionPK,
        };
      }

      //socket.emit(socketEvents.USER_MESSAGE, payload);
      sendUserMessage.mutate(payload);
    }

    setTimeout(
      () => scrollToLastMsg(allMessages[allMessages.length - 1].id),
      100
    );

    setChatState({
      messages: allMessages,
      waitingForServer: true,
      inputDisabled: true,
      focusInput: false,
    });
  };

  const textEditHandler = (value: string) => {
    setChatState({
      prompt: value,
    });
  };

  const textEditEnd = () => {
    setChatState({
      prompt: "",
    });
  };

  const onApproveTool = () => {


    // add new message "ok" and disable "waiting for answer..."
    let allMessages = messages;
    const currentMessageId = messages.length;

    const newMessage = {
      id: currentMessageId,
      from: "user",
      content: "ok",
      type: "message",
    };
    allMessages = [...allMessages, newMessage];

    setTimeout(
      () => scrollToLastMsg(allMessages[allMessages.length - 1].id),
      100
    );

    setChatState({
      messages: allMessages,
      waitingForServer: true,
      inputDisabled: true,
      focusInput: false,
    });

    // send approval to server
    const payload = {
      datetime: new Date().toISOString(),
      task_tool_execution_pk: messages[messages.length - 1].task_tool_execution_fk,
    };

    sendTaskToolExecutionApproval.mutate(payload, {
      onSuccess: () => {
        showPopup();
      },
    });

  };


  const onRejectTool = () => {
    // remove task_tool_execution_fk from last message
    let allMessages = messages;
    allMessages[allMessages.length - 1].task_tool_execution_fk = null;

    setChatState({
      messages: allMessages,
      inputDisabled: false,
      focusInput: true,
    });
  };


  // print last message if there is one
  if (messages.length > 0) {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.task_tool_execution_fk) {
      return <ChatAcceptToolButtons
        onApproveTool={onApproveTool}
        onRejectTool={onRejectTool}
      />;
    }
  }


  return (
    <ChatInput
      onSend={sendMessage}
      inputDisabled={inputDisabled}
      isMobile={isMobile}
      focusInput={focusInput}
      textEdit={textEditHandler}
      textEditEnd={textEditEnd}
      prompt={prompt}
      initial_msg={initialMsg}
    />

  );

};

export default ChatAction;
