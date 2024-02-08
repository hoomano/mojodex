import { useEffect, useContext, useRef } from "react";
import { io } from "socket.io-client";
import ChatContext from "../helpers/ChatContext";
import { envVariable } from "helpers/constants/env-vars";
import { socketEvents } from "helpers/constants/socket";
import { appVersion } from "helpers/constants/index";
import { getSession } from "next-auth/react";
import { ChatContextType, ChatUsedFrom } from "../interface/context";
import { MessageType } from "../interface";

const useSocket = () => {
  const mojoMessageCallbackRef: any = useRef();
  const mojoTokenCallbackRef: any = useRef();

  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;

  const { sessionId, messages, isMobile, chatUsedFrom } = chatState;

  mojoMessageCallbackRef.current = (msg: MessageType) => {
    try {
      // If we receive old message, do not proceed further
      if (msg?.message_pk) {
        const oldMsgFound = messages.find(
          (oldMsg: any) =>
            oldMsg.from === "agent" && oldMsg.id === msg.message_pk
        );

        if (oldMsgFound) {
          return;
        }
      }

      let allMessages = [...messages];
      // if last message is from mojo, replace question with msg.text, else, add new message
      if (
        allMessages.length > 0 &&
        allMessages[allMessages.length - 1].from === "agent" &&
        allMessages[allMessages.length - 1]?.isMojoToken
      ) {
        allMessages[allMessages.length - 1].question = msg.text;
        allMessages[allMessages.length - 1].content =
          msg.text + "\n" + allMessages[allMessages.length - 1].content;
        // add produced_text to the message
        allMessages[allMessages.length - 1].produced_text = msg.produced_text;
        allMessages[allMessages.length - 1].id = msg.message_pk;
      } else {
        const newMessage = {
          id: msg.message_pk,
          from: "agent",
          content: msg.text,
          type: "mojo_message",
          question:
            chatUsedFrom === ChatUsedFrom.Chat
              ? msg.text
              : msg?.question || msg.text,
          produced_text: msg.produced_text,
          source: msg?.source,
          answer: msg?.answer,
          messageFor: chatUsedFrom,
          tool_execution_fk: msg?.tool_execution_fk,
          showTaskMessage:
            chatUsedFrom === ChatUsedFrom.Task &&
            msg?.question &&
            msg?.tool_execution_fk,
        };
        allMessages = [...allMessages, newMessage];
      }
      setChatState({
        messages: allMessages,
        waitingForServer: false,
        inputDisabled: !!msg?.answer,
        focusInput: !isMobile
      });
    } catch (error) {
      console.error("🔴 Error parsing ask human message: " + error);
    }
  };

  mojoTokenCallbackRef.current = (msg: MessageType) => {
    try {
      let allMessages = messages;
      // if last message is from mojo, replace question with msg.text, else, add new message
      if (
        allMessages.length > 0 &&
        allMessages[allMessages.length - 1].from === "agent" &&
        allMessages[allMessages.length - 1]?.isMojoToken
      ) {
        allMessages[allMessages.length - 1].question = msg.text;
        allMessages[allMessages.length - 1].content =
          msg.text + "\n" + allMessages[allMessages.length - 1].content;
      } else {
        const currentMessageId = messages.length;
        const newMessage = {
          id: currentMessageId,
          from: "agent",
          content: msg.text,
          type: "mojo_message",
          question: msg.text,
          produced_text: msg.produced_text,
          isMojoToken: true,
        };
        allMessages = [...allMessages, newMessage];
      }
      setChatState({
        messages: allMessages,
        waitingForServer: false,
        inputDisabled: true,
      });
    } catch (error) {
      console.error("🔴 Error parsing mojo message: " + error);
    }
  };



  const showErrorNotification = (error: string) => {
    setChatState({
      showSnackBar: true,
      messageSnackBar: error,
    });
  };

  const initSession = async () => {
    const { authorization } = (await getSession()) as any;
    const token = authorization?.token;
    if (!envVariable.socketUrl) {
      return;
    }
    const socket = io(envVariable.socketUrl, {
      transports: ["websocket"],
      auth: {
        token: token,
      },
    });
    socket.on(socketEvents.CONNECT, () => {
      console.log("🟢 Socket connected");
      socket.emit(
        socketEvents.START_SESSION,
        { session_id: sessionId, version: appVersion },
        () => { }
      );
    });
    socket.on(socketEvents.MOJO_TOKEN, (msg) =>
      mojoTokenCallbackRef.current(msg)
    );
    socket.on(socketEvents.MOJO_MESSAGE, (msg, ack) => {
      mojoMessageCallbackRef.current(msg);
      if (ack) {
        ack({
          session_id: sessionId,
          message_pk: msg?.message_pk,
        });
      }
    });

    socket.on(socketEvents.DISCONNECT, () => {
      console.log("🔴 Socket disconnected");
    });
    socket.on(socketEvents.ERROR, (err) => {
      console.log("🔴 Server error received: " + JSON.stringify(err));
      showErrorNotification(JSON.stringify(err));
    });
    socket.on(socketEvents.CONNECT_ERROR, (err) => {
      console.log("🔴 Socket connect_error: " + err.message);
      if (err.message === "Expired token") {
        return;
      } else {
        console.error("🔴 Server error received: " + err.message);
        showErrorNotification(err.message);
      }
    });
    socket.on(socketEvents.CONNECT_TIMEOUT, (err) => {
      console.debug("🔴 Socket connect_timeout: " + err.message);
      showErrorNotification(err.message);
    });
    setChatState({
      socket,
    });
  };

  useEffect(() => {
    if (sessionId) {
      initSession();
    }
  }, [sessionId]);
};
export default useSocket;
