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


function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface StepProcessDetailProps {
  taskExecution: UserTaskExecution;
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  taskExecution,
}) => {
  const router = useRouter();

  // // currentTaskExecution will be updated later with socketio event. We prepare the REACT state for it.
  // // initialize its value with the data from useGetExecuteTaskById
  const [currentTaskExecution, setCurrentTaskExecution] = useState(taskExecution);
  console.log("Current task execution: ", currentTaskExecution);

  const workflowStatus = "Ongoing";

  const [isSocketLoaded, setIsSocketLoaded] = useState(false);



  useEffect(() => {
    if (!isSocketLoaded) {
      initializeSocket();
    }
  }, [isSocketLoaded]);


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

    const sessionId = currentTaskExecution?.session_id;
    console.log("🔵 STEP PROCESS DETAIL initializeSocket sessionId ", sessionId);
    socket.on(socketEvents.CONNECT, () => {
      console.log("🔵 STEP PROCESS DETAIL Connected to socket")
      socket.emit(socketEvents.START_SESSION, {
        session_id: sessionId,
        version: appVersion,
      });
    });

    socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_STARTED, (msg) => {
      console.log("🔵 STEP PROCESS DETAIL Workflow step execution started", msg);

       const stepExecution: UserTaskExecutionStepExecution = {
         user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
         workflow_step_pk: msg.workflow_step_pk,
         step_name_for_user: msg.step_name_for_user,
         step_definition_for_user: msg.step_definition_for_user,
         validated: msg.validated,
         parameter: msg.parameter,
         result: msg.result
       }


       setCurrentTaskExecution((prev: UserTaskExecution) => {
         // find the step_execution with the same workflow_step_pk
         const stepExecutionIndex = prev.step_executions?.findIndex((step) => step.workflow_step_pk === msg.workflow_step_pk);
         if(stepExecutionIndex !== -1) {
           // if found, update the step_execution with the new data
           const newTaskExecution = { ...prev };
           newTaskExecution.step_executions[stepExecutionIndex] = stepExecution;
           return newTaskExecution;
         } else {
            // if not found, add the new step_execution to the list
            const newTaskExecution = { ...prev };
            newTaskExecution.step_executions?.push(stepExecution);
            return newTaskExecution;
          }
       });
       console.log("Current task execution: ", currentTaskExecution);


    });

    socket.on(socketEvents.WORKFLOW_STEP_EXECUTION_ENDED, (msg) => {
      console.log("🔵 STEP PROCESS DETAIL Workflow step execution ended", msg);

      const stepExecution: UserTaskExecutionStepExecution = {
        user_workflow_step_execution_pk: msg.user_workflow_step_execution_pk,
        workflow_step_pk: msg.workflow_step_pk,
        step_name_for_user: msg.step_name_for_user,
        step_definition_for_user: msg.step_definition_for_user,
        validated: msg.validated,
        parameter: msg.parameter,
        result: msg.result
      }
      
      setCurrentTaskExecution((prev: UserTaskExecution) => {
        // find the step_execution with the same workflow_step_pk
        const stepExecutionIndex = prev.step_executions?.findIndex((step) => step.workflow_step_pk === msg.workflow_step_pk);
        if (stepExecutionIndex !== -1) {
          // if found, update the step_execution with the new data
          const newTaskExecution = { ...prev };
          newTaskExecution.step_executions[stepExecutionIndex] = stepExecution;
          return newTaskExecution;
        } else {
          // if not found, add the new step_execution to the list
          const newTaskExecution = { ...prev };
          newTaskExecution.step_executions?.push(stepExecution);
          return newTaskExecution;
        }
      });
      console.log("Current task execution: ", currentTaskExecution);

    });


  };

  const onUndoStep = (event: React.MouseEvent<HTMLButtonElement>) => {
    //event.stopPropagation();
    console.log("Undo step");
  };

  const onContinueStep = (event: React.MouseEvent<HTMLButtonElement>) => {
    //event.stopPropagation();
    console.log("Continue step");
  };

  return (
    <div className="p-[60px]">
        <div>
          <div className="text-h4 font-semibold text-gray-darker">
            Workflow: {currentTaskExecution.user_task_execution_pk}
          </div>
          <div className="text-subtitle6 font-semibold text-gray-lighter">
            {workflowStatus}
          </div>

      </div>

      <ul role="list" className="space-y-6">
        {currentTaskExecution?.step_executions?.map((stepItem, activityItemIdx) => (
          <li key={stepItem.workflow_step_pk} className="relative flex gap-x-4">
            <div
              className={classNames(
                activityItemIdx === currentTaskExecution?.step_executions.length - 1 ? 'h-6' : '-bottom-6',
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
                <span className="block text-gray-400">{JSON.stringify(stepItem.parameter)}</span>
                <span className="block text-gray-400">{JSON.stringify(stepItem.result)}</span>
              </p>
            </>
            {stepItem.validated === null ? <div className="text-end">
              <Button
                variant="outline"
                size="middle"
                onClick={onUndoStep}
                className="mr-2"
              >
                Delete
              </Button>

              <Button variant="primary" size="middle" onClick={onContinueStep}>
                Run
              </Button>
            </div> : null
            }
          </li>
        ))}
      </ul>

    </div>
  );
};

export default StepProcessDetail;