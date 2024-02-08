import { useMutation } from "@tanstack/react-query";
import { deleteChat } from "services/chat";

const useDeleteChat = () => useMutation(deleteChat);

export default useDeleteChat;
