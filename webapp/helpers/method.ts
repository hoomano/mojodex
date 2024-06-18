import { MessageType } from "modules/Chat/interface";
import { ChatUsedFrom } from "modules/Chat/interface/context";

export const classNames = (...classes: any) =>
  classes.filter(Boolean).join(" ");

export const debounce = (func: Function, timeout = 300) => {
  let timer: any;
  return (...args: any) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
};

export const encryptId = (id?: number | string) =>
  id ? window.btoa(id.toString()) : null;

export const decryptId = (id: number | string) => {
  try {
    return +window.atob(id.toString());
  } catch (error) {
    return null;
  }
};

export const updateTaskMessageFormat = (
  messages: { sender: string; message: MessageType }[],
  chatUsedFrom: ChatUsedFrom | null
) => {
  let formattedMessages: any = [];

  messages.reverse().forEach(({ sender, message }) => {
    if (!message?.error) {
      if (sender === "mojo") {
        if (!message?.produced_text_pk) {
          formattedMessages.push({
            id: Math.random(),
            from: "agent",
            content: message.text,
            type: "mojo_message",
            question:
              chatUsedFrom === ChatUsedFrom.Chat
                ? message.text
                : message?.question || message.text,
            produced_text: message.produced_text,
            source: message?.source,
            answer: message?.answer,
            messageFor: chatUsedFrom
          });
        }
      } else if (sender === "user") {
        formattedMessages.push({
          id: Math.random(),
          from: "user",
          content: message?.text,
          type: "message",
        }); 
      } // else, sender == system, won't be displayed
    }
  });

  return formattedMessages;
};
