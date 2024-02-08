import React, { useContext, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPencilAlt,
  faTrashAlt,
  faCheck,
  faClose,
} from "@fortawesome/free-solid-svg-icons";
import useDeleteChat from "../hooks/useDeleteChat";
import useUpdateChatTitle from "../hooks/useUpdateChatTitle";
import { ChatSession } from "../interface";
import useGetChatHistory from "../hooks/useGetChatHistory";
import queryClient, { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { useRouter } from "next/router";
import { debounce } from "helpers/method";
import Loader from "components/Loader";
import useAlert from "helpers/hooks/useAlert";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";

interface ChatHistoryProps {}

const ChatHistory = ({}: ChatHistoryProps) => {
  const router = useRouter();
  const deleteChat = useDeleteChat();
  const updateChatTitle = useUpdateChatTitle();
  const [editData, setEditData] = useState<null | ChatSession>(null);
  const { showAlert } = useAlert();

  const { globalState } = useContext(globalContext) as GlobalContextType;

  const {
    fetchNextPage,
    data: sessionResponse,
    isFetching,
  } = useGetChatHistory();

  const onChatTitleUpdate = (sessionId: string) => {
    const payload = {
      datetime: new Date().toISOString(),
      session_id: sessionId,
      title: editData?.title || "",
    };

    updateChatTitle.mutate(payload, {
      onSuccess: () => {
        showAlert({
          title: "Title updated successfully.",
          type: "success",
        });
        setEditData(null);
        invalidateQuery([cachedAPIName.CHAT_HISTORY]);

        queryClient.setQueryData([cachedAPIName.CHAT_HISTORY], (prev: any) => {
          prev.pages.forEach((item: any) => {
            item.sessions.forEach((session: any) => {
              if (editData?.session_id === session.session_id) {
                session.title = editData?.title;
              }
            });
          });
          return prev;
        });
      },
      onError: (error: any) => {
        showAlert({
          title: error?.error,
          type: "primary",
        });
      },
    });
  };

  const onDeleteChat = (session_id: string) => {
    deleteChat.mutate(session_id, {
      onSuccess: () => {
        showAlert({
          title: "Chat deleted successfully.",
          type: "success",
        });
        invalidateQuery([cachedAPIName.CHAT_HISTORY]);
        router.push("/");
      },
      onError: (error: any) => {
        showAlert({
          title: error,
          type: "error",
        });
      },
    });
  };

  const sessionList =
    sessionResponse?.pages?.flatMap((data) => data.sessions) || [];

  const handleRefetchOnScrollEnd = async (e: any) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (!isFetching && scrollHeight - scrollTop <= clientHeight * 1.2) {
      await fetchNextPage({ pageParam: sessionList.length });
    }
  };

  return (
    <div
      className="mt-1 h-full max-h-[300px] overflow-auto"
      onScroll={debounce(handleRefetchOnScrollEnd)}
    >
      {sessionList?.map((chat) => {
        if (!chat.title) return null;

        const isSessionSelected = router.query?.sessionId === chat.session_id;

        return (
          <div
            className={`text-gray-light flex items-center justify-between cursor-pointer px-2 py-3 ${
              isSessionSelected
                ? "rounded-md gap-2 bg-[rgba(52,53,65,var(--tw-bg-opacity))]"
                : "opacity-50"
            }`}
            key={chat.session_id}
          >
            {chat.session_id === editData?.session_id ? (
              <input
                id="title"
                name="title"
                type="text"
                value={editData?.title || ""}
                onChange={(e) =>
                  setEditData({
                    session_id: editData?.session_id,
                    title: e.target.value,
                  })
                }
                autoFocus
                className="w-full bg-transparent border-0 text-white text-sm p-0"
              />
            ) : (
              <div
                onClick={() => {
                  router.push({
                    pathname: "/",
                    query: { ...router.query, sessionId: chat.session_id },
                  });

                  if (globalState?.mainChatInputRef) {
                    globalState.mainChatInputRef.focus();
                  }
                }}
                className="text-sm whitespace-nowrap text-ellipsis overflow-hidden w-[180px]"
              >
                {chat.title}
              </div>
            )}

            {isSessionSelected && (
              <div className="flex gap-2.5 mr-1">
                {chat.session_id === editData?.session_id ? (
                  <>
                    <FontAwesomeIcon
                      icon={faCheck}
                      className="text-white w-3 h-3"
                      onClick={() => onChatTitleUpdate(editData?.session_id)}
                    />
                    <FontAwesomeIcon
                      icon={faClose}
                      className="text-white w-3 h-3"
                      onClick={() => setEditData(null)}
                    />
                  </>
                ) : (
                  <>
                    <FontAwesomeIcon
                      icon={faPencilAlt}
                      className="text-white w-3 h-3"
                      onClick={() => setEditData(chat)}
                    />
                    <FontAwesomeIcon
                      icon={faTrashAlt}
                      className="text-white w-3 h-3"
                      onClick={() => onDeleteChat(chat.session_id)}
                    />
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}

      {isFetching && <Loader color="white" />}
    </div>
  );
};

export default ChatHistory;
