import { GetChatHistoryResponse, ChatSession, UserMessagePayload } from "modules/Chat/interface";
import { apiRoutes } from ".";
import axiosClient from "./config/axiosClient";

export const getChatHistory = ({
  pageParam = 0,
}: any): Promise<GetChatHistoryResponse> =>
  axiosClient.get(apiRoutes.chatHistory, {
    params: { learned_by_mojo: false, n_sessions: 10, offset: pageParam },
  });

export const updateChatTitle = (payload: ChatSession) =>
  axiosClient.post(apiRoutes.editChat, payload);

export const deleteChat = (session_id: string) =>
  axiosClient.delete(apiRoutes.deleteChat, {
    params: { session_id: session_id },
  });

export const sendUserMessage = (payload: UserMessagePayload) => {
  const formData = new FormData();
  (Object.keys(payload) as Array<keyof UserMessagePayload>).forEach(key => {
    const value = payload[key];
    if (value !== undefined) {
      formData.append(key, value.toString()); // Assuming all values can be safely converted to strings
    }
  });

  // Send the form data using axios PUT request
  return axiosClient.put(apiRoutes.sendUserMessage, formData);
};

