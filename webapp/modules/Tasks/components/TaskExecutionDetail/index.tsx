import React, { useContext, useEffect, useRef, useState } from "react";
import { getSession } from "next-auth/react";
import { useRouter } from "next/router";
import { io } from "socket.io-client";
import globalContext from "helpers/GlobalContext";
import { GlobalContextType } from "helpers/GlobalContext";
import { appVersion } from "helpers/constants";
import { envVariable } from "helpers/constants/env-vars";
import { decryptId } from "helpers/method";
import useGetDraft from "modules/Drafts/hooks/useGetDraft";
import { EditerDraft } from "modules/Tasks/interface";
import usePostExecuteTask from "modules/Tasks/hooks/usePostExecuteTask";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import Tab, { TabType } from "components/Tab";
import Result from "./Result";
import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import useGetTask from "modules/Tasks/hooks/useGetTask";
import { socketEvents } from "helpers/constants/socket";
import ChatContext from "modules/Chat/helpers/ChatContext";
import Chat from "modules/Chat";
import { ChatContextType } from "modules/Chat/interface/context";
import TaskLoader from "./TaskLoader";
import Todos from "./Todos";
import { useTranslation } from "react-i18next";

const DraftDetail = () => {
  const [tabs, setTabs] = useState<TabType[]>([]);
  const [selectedTab, setSelectedTab] = useState("result");
  const router = useRouter();

  const messagePkRef = useRef<number[]>([]);

  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;

  const taskId = router.query?.taskId
    ? decryptId(router.query.taskId as string)
    : null;

  const taskExecutionPK = router.query?.taskExecutionPK
    ? decryptId(router.query.taskExecutionPK as string)
    : null;

  useEffect(() => {
    if (taskExecutionPK) {
      setChatState({
        currentTaskInfo: {
          taskExecutionPK,
          text: chatState?.currentTaskInfo?.text || "",
          textPk: chatState?.currentTaskInfo?.textPk || null,
          title: chatState?.currentTaskInfo?.title || "",
        },
      });
    }
  }, [taskExecutionPK]);

  const {
    globalState: { newlyCreatedTaskInfo },
    setGlobalState,
  } = useContext(globalContext) as GlobalContextType;

  const { data: taskDetail } = useGetTask(taskId);
  const { data: currentTask } = useGetExecuteTaskById(taskExecutionPK, {
    enabled: !taskId && !!taskExecutionPK,
  });
  const { data: draftDetails, isFetching: isDraftLoading } = useGetDraft(
    taskId,
    { enabled: !newlyCreatedTaskInfo && !!taskId }
  );
  const { mutate: executeTaskMutation, isLoading: isPostExecuteTaskLoading } =
    usePostExecuteTask();

  const [isSocketLoaded, setIsSocketLoaded] = useState(false);
  const [isTask, setIsTask] = useState(false);
  const [streamTitle, setStreamTitle] = useState<string | null>(null);
  const [editorDetails, setEditorDetails] = useState<EditerDraft>({
    text: "",
    title: "",
    textPk: null,
  });
  const { t } = useTranslation("dynamic");

  useEffect(() => {
    return () => setGlobalState({ newlyCreatedTaskInfo: null });
  }, []);

  useEffect(() => {
    let tabs = [
      {
        key: "result",
        title: `${t("userTaskExecution.resultTab.title")}`,
        component: (
          <Result
            userTaskExecutionPk={taskExecutionPK as number}
            task={editorDetails}
            isLoading={isPostExecuteTaskLoading || isDraftLoading}
            isTask={isTask}
          />
        ),
      },
      {
        key: "todos",
        title: `${t("userTaskExecution.todosTab.title")}`,
        component: (
          <Todos
            taskExecutionPK={taskExecutionPK as number}
            workingOnTodos={currentTask?.working_on_todos}
            nTodos={currentTask?.n_todos}
          />
        ),
      },
    ];

    setTabs(tabs);

    if (router.query.tab === "todos") {
      setSelectedTab("todos");
    } else {
      setSelectedTab("result");
    }
  }, [editorDetails, isTask, router.query.tab]);

  useEffect(() => {
    if (draftDetails) {
      setEditorDetails({
        text: draftDetails?.production,
        title: draftDetails?.title,
        textPk: draftDetails?.produced_text_pk,
      });
    }

    if (currentTask) {
      setEditorDetails({
        text: currentTask.produced_text_production,
        title: currentTask?.produced_text_title,
        textPk: currentTask?.produced_text_pk,
      });
    }
  }, [draftDetails, currentTask]);

  // TODO: Do we need this validation
  // useEffect(() => {
  //   if (!newlyCreatedTaskInfo?.sessionId && taskId) {
  //     router.push(`/tasks/create/${encryptId(taskId as number)}`);
  //   }
  // }, [newlyCreatedTaskInfo?.sessionId]);

  useEffect(() => {
    if (!isSocketLoaded && (newlyCreatedTaskInfo || currentTask?.session_id)) {
      initializeSocket();
      setIsTask(true);
    }
  }, [isSocketLoaded, currentTask?.session_id, newlyCreatedTaskInfo]);

  const initializeSocket = async () => {
    if (
      currentTask?.user_task_execution_pk ||
      newlyCreatedTaskInfo?.sessionId
    ) {
      setIsSocketLoaded(true);

      const session: any = await getSession();
      const token = session?.authorization?.token || "";

      const socket = io(envVariable.socketUrl as string, {
        transports: ["websocket"],
        auth: {
          token,
        },
      });

      const sessionId =
        currentTask?.session_id || newlyCreatedTaskInfo?.sessionId;

      socket.emit(socketEvents.START_SESSION, {
        session_id: sessionId,
        version: appVersion,
      });

      socket.on(socketEvents.DRAFT_TOKEN, ({ text }) => {
        setEditorDetails((prev) => ({ ...prev, text }));
      });

      socket.on(socketEvents.USER_TASK_EXECUTION_TITLE, ({ title }) => {
        setStreamTitle(title);
      });

      socket.on(socketEvents.DRAFT_MESSAGE, (message: any, ack) => {
        if (messagePkRef.current.includes(message?.message_pk)) {
          return;
        } else {
          messagePkRef.current.push(message?.message_pk);
        }

        const {
          produced_text,
          produced_text_pk,
          produced_text_title,
          user_task_execution_pk,
        } = message;

        setEditorDetails({
          text: produced_text,
          title: produced_text_title,
          textPk: produced_text_pk,
        });

        setChatState({
          currentTaskInfo: {
            taskExecutionPK: user_task_execution_pk,
            text: produced_text,
            textPk: produced_text_pk,
            title: produced_text_title,
          },
          inputDisabled: false,
          waitingForServer: false,
        });

        if (ack) {
          ack({
            session_id: sessionId,
            message_pk: message?.message_pk,
            produced_text_version_pk: message?.produced_text_version_pk,
          });
        }
      });

      if (newlyCreatedTaskInfo) {
        const { inputArray, taskExecutionPK } = newlyCreatedTaskInfo;

        executeTaskMutation(
          {
            datetime: new Date().toISOString(),
            user_task_execution_pk: taskExecutionPK,
            inputs: inputArray,
          },
          {
            onSuccess: (data) => {
              setEditorDetails({
                text: data.produced_text,
                title: data.produced_text_title,
                textPk: data.produced_text_pk,
              });
            },
          }
        );
      }
    }
  };

  return (
    <div className="flex relative">
      <div className="flex-1 p-8 lg:p-16 h-[calc(100vh-72px)] lg:h-screen overflow-auto">
        {!editorDetails?.text ? (
          <TaskLoader />
        ) : (
          <>
            <div className="flex items-center mb-5">
              <ArrowLeftIcon
                onClick={() => router.push(`/tasks`)}
                className="w-[24px] h-[24px] text-gray-lighter cursor-pointer mr-2"
              />
              <div>
                <div className="text-subtitle6 font-semibold text-gray-lighter">
                  {taskDetail?.task_name || currentTask?.task_name}
                </div>
                {!!streamTitle && (
                  <div className="text-h4 font-semibold text-gray-darker">
                    {streamTitle}
                  </div>
                )}
              </div>
            </div>
            <Tab
              selected={selectedTab}
              onChangeTab={(key: string) => setSelectedTab(key)}
              tabs={tabs}
              isDisable={!currentTask?.produced_text_production ? true : false}
              notReadTodos={currentTask?.n_not_read_todos}
            />
          </>
        )}
      </div>
      <div className="sticky top-0 left-0 h-[calc(100vh-72px)] lg:h-screen w-[345px] text-white">
        <Chat />
      </div>
    </div>
  );
};

export default DraftDetail;
