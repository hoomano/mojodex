import {
  ArrowLeftIcon,
} from "@heroicons/react/24/outline";
import { UserTask, UserTaskExecutionStepExecution, UserTaskExecution } from "modules/Tasks/interface";
import { useRouter } from "next/router";
import { useState, useContext, useEffect } from "react";

import globalContext from "helpers/GlobalContext";
import { GlobalContextType } from "helpers/GlobalContext";
import { getSession } from "next-auth/react";
import { envVariable } from "helpers/constants/env-vars";
import { appVersion } from "helpers/constants";

import { io } from "socket.io-client";
import { socketEvents } from "helpers/constants/socket";
import usePostExecuteTask from "modules/Tasks/hooks/usePostExecuteTask";
import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import Button from "components/Button";

import { Fragment } from 'react'
import { CheckCircleIcon } from '@heroicons/react/24/solid'
import {
  FaceFrownIcon,
  FaceSmileIcon,
  FireIcon,
  HandThumbUpIcon,
  HeartIcon,
  PaperClipIcon,
  XMarkIcon,
} from '@heroicons/react/20/solid'
import { Listbox, Transition } from '@headlessui/react'



const activity = [
  { id: 1, type: 'created', person: { name: 'Chelsea Hagon' }, date: '7d ago', dateTime: '2023-01-23T10:32' },
  { id: 2, type: 'edited', person: { name: 'Chelsea Hagon' }, date: '6d ago', dateTime: '2023-01-23T11:03' },
  {
    id: 4,
    type: 'finished',
    person: {
      name: 'Mojodex',
    },
    produced_text: "Topic of stanza 1: The moon's appearance in the spring sky",
    date: '3d ago',
    dateTime: '2023-01-23T15:56',
  },
]

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export interface ProcessStep {
  step_pk: number;
  index: number;
  description: string;
  assigned_to: string;
  placeholder: string;
  delivery?: string;
  achieved: boolean;
  delivery_date?: string;
}

export interface ProcessStepResponse {
  description: string;
  launched: boolean;
  achieved: boolean;
  steps: ProcessStep[];
  progress: 0;
}

interface StepProcessDetailProps {
  task?: UserTask;
  taskExecutionPK?: number;
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  task,
  taskExecutionPK,
}) => {
  const router = useRouter();
  const [expanded, setExpanded] = useState<Record<string, string>>({});

  const {
    globalState: { newlyCreatedTaskInfo },
    setGlobalState,
  } = useContext(globalContext) as GlobalContextType;

  const { data: initTaskExecution } = useGetExecuteTaskById(taskExecutionPK, {
    enabled: !task?.user_task_pk && !!taskExecutionPK,
  });

  // currentTaskExecution will be updated later with socketio event. We prepare the REACT state for it.
  // initialize its value with the data from useGetExecuteTaskById
  const [currentTaskExecution, setCurrentTaskExecution] = useState(initTaskExecution);


  const onGoingProcessIndex = 0;

  const workflowStatus = "Ongoing";

  const [isSocketLoaded, setIsSocketLoaded] = useState(false);

  const { mutate: executeTaskMutation, isLoading: isPostExecuteTaskLoading } =
    usePostExecuteTask();
  // Create a mock data of ProcessStepResponse with 2 steps:
  // 1. step_pk: 1, description: "Step 1", assigned_to: "USER", placeholder: "Placeholder 1", delivery: "Delivery 1", achieved: false, delivery_date: "2022-10-10"
  // 2. step_pk: 2, description: "Step 2", assigned_to: "USER", placeholder: "Placeholder 2", delivery: "Delivery 2", achieved: false, delivery_date: "2022-10-10"

  const data = {
    description: "Description",
    launched: true,
    achieved: false,
    steps: [
      {
        step_pk: 1,
        index: 0,
        description: "Step 1",
        assigned_to: "USER",
        placeholder: "Placeholder 1",
        delivery: "Delivery 1",
        achieved: true,
        delivery_date: "2022-10-10",
      },
      {
        step_pk: 2,
        index: 1,
        description: "Step 2",
        assigned_to: "USER",
        placeholder: "Placeholder 2",
        delivery: "Delivery 2",
        achieved: false,
        delivery_date: "2022-10-10",
      },
    ],
    progress: 0,
  };

  useEffect(() => {
    return () => setGlobalState({ newlyCreatedTaskInfo: null });
  }, []);


  useEffect(() => {
    if (!isSocketLoaded && (newlyCreatedTaskInfo || currentTaskExecution?.session_id)) {
      initializeSocket();
    }
  }, [isSocketLoaded, currentTaskExecution?.session_id, newlyCreatedTaskInfo]);


  const initializeSocket = async () => {
    if (
      newlyCreatedTaskInfo?.sessionId
    ) {
      setIsSocketLoaded(true);

      const session: any = await getSession();
      const token = session?.authorization?.token || "";
      console.log("token: ", token);

      const socket = io(envVariable.socketUrl as string, {
        transports: ["websocket"],
        auth: {
          token,
        },
      });

      const sessionId = newlyCreatedTaskInfo?.sessionId;

      console.log("Current task execution steps: ", currentTaskExecution);

      socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_STARTED, (msg) => {
        console.log("Workflow step execution started", msg);

        const stepExecution: UserTaskExecutionStepExecution = {
          user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
          workflow_step_pk: msg.workflow_step_pk,
          step_name_for_user: msg.step_name_for_user,
          step_definition_for_user: msg.step_definition_for_user,
          validated: msg.validated,
          parameter: msg.parameter,
          result: msg.result
        }

        console.log("new step execution: ", stepExecution)

        setCurrentTaskExecution((prev: UserTaskExecution | undefined) => {
          if (!prev) {
            // return a new UserTaskExecution object or undefined based on your requirements
            return undefined;
          }
          const newTaskExecution = { ...prev };
          newTaskExecution.step_executions?.push(stepExecution);
          return newTaskExecution;
        })
        

      });

      socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_ENDED, (msg) => {

        const stepExecution : UserTaskExecutionStepExecution = {
          user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
          workflow_step_pk: msg.workflow_step_pk,
          step_name_for_user: msg.step_name_for_user,
          step_definition_for_user: msg.step_definition_for_user,
          validated: msg.validated,
          parameter: msg.parameter,
          result: msg.result
        }

        setCurrentTaskExecution((prev: UserTaskExecution | undefined) => {
          if (!prev) {
            // return a new UserTaskExecution object or undefined based on your requirements
            return undefined;
          }
          const newTaskExecution = { ...prev };
          newTaskExecution.step_executions?.push(stepExecution);
          return newTaskExecution;
        })

        console.log("Current task execution: ", currentTaskExecution?.step_executions)
        
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
            onSuccess: (data: any) => {
              console.log("Task executed successfully", data);
              socket.emit(socketEvents.START_SESSION, {
                session_id: sessionId,
                version: appVersion,
              });
            },
          }
        );
      }
    }
  };

  const onUndoStep = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    console.log("Undo step");
  };

  const onContinueStep = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    console.log("Continue step");
  };

  return (
    <div className="p-[60px]">
      <div className="flex items-center mb-[30px]">
        <ArrowLeftIcon
          onClick={() => router.back()}
          className="w-[24px] h-[24px] text-gray-lighter cursor-pointer mr-2"
        />
        <div>
          <div className="text-h4 font-semibold text-gray-darker">
            Workflow: {taskExecutionPK}
          </div>
          <div className="text-subtitle6 font-semibold text-gray-lighter">
            {workflowStatus}
          </div>
        </div>
      </div>

      <ul role="list" className="space-y-6">
        {currentTaskExecution?.step_executions?.map((stepItem, activityItemIdx) => (
          <li key={stepItem.workflow_step_pk} className="relative flex gap-x-4">
            <div
              className={classNames(
                activityItemIdx === activity.length - 1 ? 'h-6' : '-bottom-6',
                'absolute left-0 top-0 flex w-6 justify-center'
              )}
            >
              <div className="w-px bg-gray-200" />
            </div>
              <>
                <div className="relative flex h-6 w-6 flex-none items-center justify-center bg-white">
                  
                    <div className="h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                </div>
                <p className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                  <span className="font-medium text-gray-900">{stepItem.step_name_for_user}: {stepItem.step_definition_for_user}</span>
                  <span className="block text-gray-400">{stepItem.validated ? "Validated" : "Not validated"}</span>
                  <span className="block text-gray-400">{stepItem.parameter}</span>
                  <span className="block text-gray-400">{stepItem.result}</span>
                </p>
              </>
          </li>
        ))}
      </ul>

    </div>
  );
};

export default StepProcessDetail;