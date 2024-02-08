import { useMutation } from "@tanstack/react-query";
import { updateChatTitle } from "services/chat";

const useUpdateChatTitle = () => useMutation(updateChatTitle);

export default useUpdateChatTitle;
