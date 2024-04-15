import React, { useContext, useEffect, useRef, useState } from "react";
import { getSession } from "next-auth/react";
import { useRouter } from "next/router";
import { Socket, io } from "socket.io-client";
import { appVersion } from "helpers/constants";
import { envVariable } from "helpers/constants/env-vars";
import { decryptId } from "helpers/method";
import useGetProducedText from "modules/ProducedTexts/hooks/useGetProducedText";
import { EditerProducedText, UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import Tab, { TabType } from "components/Tab";
import Result from "./Result";
import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import { socketEvents } from "helpers/constants/socket";
import ChatContext from "modules/Chat/helpers/ChatContext";
import { ChatContextType } from "modules/Chat/interface/context";
import TodosView from "./Todos";
import { useTranslation } from "react-i18next";
import StepProcessDetail from "./Workflow/StepProcessDetail";
import Chat from "modules/Chat";
import TaskLoader from "./TaskLoader";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import ExpandableCard from "components/ExpandableCard";
import TaskInputs from "./TaskInputs";

const DraftDetail = () => {
  const [tabs, setTabs] = useState<TabType[]>([]);
  const [selectedTab, setSelectedTab] = useState("result");
  const router = useRouter();

  const messagePkRef = useRef<number[]>([]);

  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;


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


  const { data: currentTask } = useGetExecuteTaskById(taskExecutionPK);

  const { data: draftDetails, isFetching: isDraftLoading } = useGetProducedText(
    currentTask?.produced_text_pk || null,
    { enabled: !!currentTask?.produced_text_pk } // enable the query only if currentTask has produced_text_pk
  );


  const [isSocketLoaded, setIsSocketLoaded] = useState(false);
  const [isTask, setIsTask] = useState(false);
  const [streamTitle, setStreamTitle] = useState<string | null>(null);
  const [editorDetails, setEditorDetails] = useState<EditerProducedText>({
    text: "",
    title: "",
    producedTextPk: null,
  });
  const [workflowStepExecutions, setWorkflowStepExecutions] = useState(currentTask!.step_executions);
  const [chatIsVisible, setChatIsVisible] = useState(currentTask!.task_type !== "workflow");

  const { t } = useTranslation("dynamic");

  useEffect(() => {

    let resultTab = {
      key: "result",
      title: `${t("userTaskExecution.resultTab.title")}`,
      component: (
        <Result
          userTaskExecutionPk={taskExecutionPK as number}
          producedText={editorDetails}
          isLoading={isDraftLoading}
        />
      ),
      // disabled if editorDetails.textPk is null
      disabled: !editorDetails.producedTextPk ? true : false
    }

    let todosTab = {
      key: "todos",
      title: `${t("userTaskExecution.todosTab.title")}`,
      component: (
        <TodosView
          taskExecutionPK={taskExecutionPK as number}
          workingOnTodos={currentTask?.working_on_todos}
          nTodos={currentTask?.n_todos}
        />
      ),
      // disabled if currentTask has no produced_text_pk
      disabled: !currentTask?.produced_text_pk ? true : false
    }

    let processTab = {
      key: "process",
      title: `${t("userTaskExecution.processTab.title")}`,
      component: (
        <StepProcessDetail stepExecutions={workflowStepExecutions!}
          onInvalidate={() => setChatIsVisible(true)}
          onValidate={(stepExecutionPk: number) => onStepExecutionValidated(stepExecutionPk)}
          onStepRelaunched={(stepExecutionPk: number) => onStepRelaunched(stepExecutionPk)}
        />
      ),
      disabled: false
    };

    let inputsTab = {
      key: "inputs",
      title: `${t("userTaskExecution.inputsTab.title")}`,
      component: (
        <TaskInputs inputs={currentTask!.json_inputs_values} />
      ),
      disabled: false
    };


    let tabs = [];
    // if currentTask.task_type !== "workflow" add todos tab
    if (currentTask?.task_type === "workflow") {
      tabs = [inputsTab, processTab, resultTab];
    } else {
      tabs = [inputsTab, resultTab, todosTab];
    }

    setTabs(tabs);

    // if selectedTab is null
    if (selectedTab === null) {
      if (router.query.tab === "todos") {
        setSelectedTab("todos");
      } else {
        if (currentTask?.task_type !== "workflow") {
          setSelectedTab("result");
        } else {
          if (editorDetails.producedTextPk) {
            setSelectedTab("result");
          } else {
            setSelectedTab("process");
          }
        }
      }
    }
  }, [workflowStepExecutions, editorDetails, isTask, router.query.tab]);

  useEffect(() => {
    if (draftDetails) {
      setEditorDetails({
        text: draftDetails?.production,
        title: draftDetails?.title,
        producedTextPk: draftDetails?.produced_text_pk,
      });
    }

    if (currentTask) {
      setEditorDetails({
        text: currentTask.produced_text_production,
        title: currentTask?.produced_text_title,
        producedTextPk: currentTask?.produced_text_pk,
      });
    }
  }, [draftDetails, currentTask]);


  useEffect(() => {
    if (!isSocketLoaded) {
      initializeSocket();
      setIsTask(true);
    }
  }, [isSocketLoaded, currentTask?.session_id]);

  const initializeSocket = async () => {

    setIsSocketLoaded(true);

    const session: any = await getSession();
    const token = session?.authorization?.token || "";

    const socket = io(envVariable.socketUrl as string, {
      transports: ["websocket"],
      auth: {
        token,
      },
    });

    const sessionId = currentTask?.session_id;

    socket.on(socketEvents.CONNECT, () => {
      socket.emit(socketEvents.START_SESSION, {
        session_id: sessionId,
        version: appVersion,
      });
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
        producedTextPk: produced_text_pk,
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

    socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_STARTED, (msg) => {

      const stepExecution: UserTaskExecutionStepExecution = {
        user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
        workflow_step_pk: msg.workflow_step_pk,
        step_name_for_user: msg.step_name_for_user,
        step_definition_for_user: msg.step_definition_for_user,
        creation_date: msg.creation_date,
        user_validation_required: msg.user_validation_required,
        validated: msg.validated,
        parameter: msg.parameter,
        result: msg.result,
        error_status: msg.error_status
      }


      setWorkflowStepExecutions((prev: UserTaskExecutionStepExecution[]) => {
        // find the step_execution with the same user_workflow_step_execution_pk
        const stepExecutionIndex = prev?.findIndex((step) => step.user_workflow_step_execution_pk === msg.user_workflow_step_execution_pk);
        if (stepExecutionIndex !== -1) {
          // if found, update the step_execution with the new data
          const newStepExecutions = [...prev];
          newStepExecutions[stepExecutionIndex] = stepExecution;
          return newStepExecutions;
        } else {
          // if not found, add the new step_execution to the list
          const newStepExecutions = [...prev];
          newStepExecutions?.push(stepExecution);
          return newStepExecutions;
        }
      });


    });

    socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_ENDED, (msg) => {

      const stepExecution: UserTaskExecutionStepExecution = {
        user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
        workflow_step_pk: msg.workflow_step_pk,
        step_name_for_user: msg.step_name_for_user,
        step_definition_for_user: msg.step_definition_for_user,
        creation_date: msg.creation_date,
        user_validation_required: msg.user_validation_required,
        validated: msg.validated,
        parameter: msg.parameter,
        result: msg.result,
        error_status: msg.error_status
      }
      setWorkflowStepExecutions((prev: UserTaskExecutionStepExecution[]) => {
        // find the step_execution with the same user_workflow_step_execution_pk
        const stepExecutionIndex = prev?.findIndex((step) => step.user_workflow_step_execution_pk === msg.user_workflow_step_execution_pk);
        if (stepExecutionIndex !== -1) {
          // if found, update the step_execution with the new data
          const newStepExecutions = [...prev];
          newStepExecutions[stepExecutionIndex] = stepExecution;
          return newStepExecutions;
        } else {
          // if not found, add the new step_execution to the list
          const newStepExecutions = [...prev];
          newStepExecutions?.push(stepExecution);
          return newStepExecutions;
        }
      });

    });

    socket.on(socketEvents.WORKFOW_STEP_EXECUTION_INVALIDATED, (msg) => {

      setWorkflowStepExecutions((prev: UserTaskExecutionStepExecution[]) => {
        // find the step_execution with the same user_workflow_step_execution_pk
        const stepExecutionIndex = prev?.findIndex((step) => step.user_workflow_step_execution_pk === msg.user_workflow_step_execution_pk);
        if (stepExecutionIndex !== -1) {
          // if found, delete the step_execution from the list
          const newStepExecutions = [...prev];
          newStepExecutions.splice(stepExecutionIndex, 1);
          return newStepExecutions;
        } else {
          return prev;
        }
      });
      setChatIsVisible(false);
    });

    socket.on(socketEvents.WORKFLOW_EXECUTION_PRODUCED_TEXT, (msg) => {

      setEditorDetails({
        text: msg.produced_text,
        title: msg.produced_text_title,
        producedTextPk: msg.produced_text_pk,
      });

    });

  };

  const onStepExecutionValidated = (user_workflow_step_execution_pk: number) => {
    // find the step_execution with the same user_workflow_step_execution_pk

    const stepExecutionIndex = workflowStepExecutions?.findIndex((step) => step.user_workflow_step_execution_pk === user_workflow_step_execution_pk);
    if (stepExecutionIndex !== -1) {
      // if found, update the step_execution with the new data
      const newStepExecutions = [...workflowStepExecutions];
      newStepExecutions[stepExecutionIndex].validated = true;
      setWorkflowStepExecutions(newStepExecutions);
    }

  }

  const onStepRelaunched = (user_workflow_step_execution_pk: number) => {
    // find the step_execution with the same user_workflow_step_execution_pk and remove it
    const stepExecutionIndex = workflowStepExecutions?.findIndex((step) => step.user_workflow_step_execution_pk === user_workflow_step_execution_pk);
    if (stepExecutionIndex !== -1) {
      // if found, delete the step_execution from the list
      const newStepExecutions = [...workflowStepExecutions];
      newStepExecutions.splice(stepExecutionIndex, 1);
      setWorkflowStepExecutions(newStepExecutions);
    }
  }

  return (
    <div className="flex relative">
      <div className="flex-1 p-8 lg:p-16 h-[calc(100vh-72px)] lg:h-screen overflow-auto">
        {
          (currentTask!.task_type !== "workflow" && !editorDetails?.text ? (
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
                    {currentTask?.task_name}
                  </div>
                  {!!streamTitle && (
                    <div className="text-h4 font-semibold text-gray-darker">
                      {streamTitle}
                    </div>
                  )}
                </div>
                </div>
                {/*<ExpandableCard headerText={t("userTaskExecution.inputsTab.title")}>
                  <TaskInputs inputs={currentTask!.json_inputs_values}/>
                </ExpandableCard>*/}
              <Tab
                selected={selectedTab}
                onChangeTab={(key: string) => setSelectedTab(key)}
                tabs={tabs}
                notReadTodos={currentTask?.n_not_read_todos}
              />
            </>
          ))
        }

      </div>
      {chatIsVisible ?
        (<div className="sticky top-0 left-0 h-[calc(100vh-72px)] lg:h-screen w-[345px] text-white">
          <Chat />
        </div>) : null}
    </div>
  );
};

export default DraftDetail;
