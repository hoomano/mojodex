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

import { Socket, io } from "socket.io-client";
import { socketEvents } from "helpers/constants/socket";
import usePostExecuteTask from "modules/Tasks/hooks/usePostExecuteTask";
import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import Button from "components/Button";


function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface StepProcessDetailProps {
  steps: any;
  stepExecutions: UserTaskExecutionStepExecution[];
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  steps,
  stepExecutions,
}) => {
  const router = useRouter();

  // // currentTaskExecution will be updated later with socketio event. We prepare the REACT state for it.
  // // initialize its value with the data from useGetExecuteTaskById
  //const [currentTaskExecution, setCurrentTaskExecution] = useState(taskExecution);
  //console.log("Current task execution: ", currentTaskExecution);
  //const[stepExecutions, setStepExecutions] = useState(step_executions);

  const workflowStatus = "Ongoing";

  const [isSocketEventInitialized, setIsSocketEventInitialized] = useState(false);



  useEffect(() => {
    if (!isSocketEventInitialized) {
      initializeSocketEvents();
    }
  }, [isSocketEventInitialized]);


  const initializeSocketEvents = async () => {
    setIsSocketEventInitialized(true);


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
            Workflow
          </div>
          <div className="text-subtitle6 font-semibold text-gray-lighter">
            {workflowStatus}
          </div>

      </div>

      <ul role="list" className="space-y-6">
        {stepExecutions?.map((stepItem, activityItemIdx) => (
          <li key={stepItem.workflow_step_pk} className="relative flex gap-x-4">
            <div
              className={classNames(
                activityItemIdx === stepExecutions.length - 1 ? 'h-6' : '-bottom-6',
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