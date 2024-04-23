import { useMutation } from "@tanstack/react-query";
import { sendUserMessage } from "services/chat";

const useSendUserMessage = () => useMutation(sendUserMessage);

export default useSendUserMessage;