import { useInfiniteQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getChatHistory } from "services/chat";

const useGetChatHistory = () =>
  useInfiniteQuery([cachedAPIName.CHAT_HISTORY], getChatHistory, {
    staleTime: 30 * 1000,
  });

export default useGetChatHistory;
