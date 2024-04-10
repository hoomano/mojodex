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
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";


import { CheckCircleIcon } from '@heroicons/react/24/solid'


const activity = [
  { id: 1, type: 'created', person: { name: 'Chelsea Hagon' }, date: '7d ago', dateTime: '2023-01-23T10:32' },
  { id: 2, type: 'edited', person: { name: 'Chelsea Hagon' }, date: '6d ago', dateTime: '2023-01-23T11:03' },
  { id: 3, type: 'sent', person: { name: 'Chelsea Hagon' }, date: '6d ago', dateTime: '2023-01-23T11:24' },
  {
    id: 4,
    type: 'commented',
    person: {
      name: 'Chelsea Hagon',
      imageUrl:
        'https://images.unsplash.com/photo-1550525811-e5869dd03032?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
    },
    comment: 'Called client, they reassured me the invoice would be paid by the 25th.',
    date: '3d ago',
    dateTime: '2023-01-23T15:56',
  },
  { id: 5, type: 'viewed', person: { name: 'Alex Curren' }, date: '2d ago', dateTime: '2023-01-24T09:12' },
  { id: 6, type: 'paid', person: { name: 'Alex Curren' }, date: '1d ago', dateTime: '2023-01-24T09:20' },
]


const workflowExecution = [
  {
    id: 1, type: 'step', name_for_user: "Stanza Divider", description_for_user: "Determines topic of each stanza",
    step_executions: [
      {
        parameters: {
          poem_topic: "moon",
          n_stanzas: 3
        },
        results: [
          {
            stanza_topic: "Topic of stanza 1: The moon's appearance in the night sky"
          },
          {
            stanza_topic: "Topic of stanza 2: The moon's influence on Earth and its creatures"
          },
          {
            stanza_topic: "Topic of stanza 3: The moon as a symbol of change and time passing"
          }
        ],
        validated: true,
      }
    ]
  },
  {
    id: 2, type: 'step', name_for_user: "Stanza Writer", description_for_user: "Writes a stanza",
    step_executions: [
      {
        parameters: {
          stanza_topic: "Topic of stanza 1: The moon's appearance in the night sky"
        },
        results: [
          {
            stanza: "The moon rises in the night sky, casting a silvery glow over the land."
          }
        ],
        validated: true,
      },
      {
        parameters: {
          stanza_topic: "Topic of stanza 2: The moon's influence on Earth and its creatures"
        },
        results: [
          {
            stanza: "The moon's pull on the tides is a powerful force, shaping the world around us."
          }
        ],
        validated: true,
      },
      {
        parameters: {
          stanza_topic: "Topic of stanza 3: The moon as a symbol of change and time passing"
        },
        results: [
          {
            stanza: "The moon waxes and wanes, a reminder of the cyclical nature of life."
          }
        ],
        validated: true,
      }
    ]
  }
]

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
  const onValidateStepExecution = useOnStepExecutionValidate();
  const onInvalidateStepExecution = useOnStepExecutionInvalidate();



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

  const onContinueStep = (user_workflow_step_execution_pk: number) => {
    //event.stopPropagation();
    console.log("Continue step");
    onValidateStepExecution.mutate(user_workflow_step_execution_pk);
  };

  return (
    <div className="p-[60px]">
      <div>
        <div className="text-h4 font-semibold text-gray-darker pb-4">
          Workflow
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
                {stepItem.validated === true ? (
                  <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                ) : (
                  <div className="h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                )}
              </div>
              <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200">
                <div className="flex justify-between gap-x-4">
                  <div className="py-0.5 text-xs leading-5 text-gray-500">
                    <span className="font-medium text-gray-900">{stepItem.step_name_for_user}: </span>{stepItem.step_definition_for_user}
                  </div>
                  <time dateTime="2024-04-10" className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                    10 sec.
                  </time>
                </div>
                {
                  Object.entries(stepItem.parameter).map(([key, value]) => (
                    <p className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                      <span className="font-medium text-gray-900">{key}:</span> {value?.toString()}
                    </p>
                  ))
                }
                {
                  // we want to iterate on each result that is a JSON object and display key value pairs
                  stepItem.result?.map((resultItem) => (
                    Object.entries(resultItem).map(([key, value]) => (
                      <p className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                        <span className="font-medium text-gray-900">{key}:</span><br /> {value?.toString()}
                      </p>
                    ))
                  ))
                }
                {stepItem.validated === null && stepItem.result != null ?
                  <div className="text-end pt-2">
                    <Button
                      variant="outline"
                      size="middle"
                      onClick={onUndoStep}
                      className="mr-2"
                    >
                      Review
                    </Button>

                    <Button variant="primary" size="middle" onClick={() => onContinueStep(stepItem.user_workflow_step_execution_pk)}>
                      Validate
                    </Button>
                  </div> : null
                }
              </div>

            </>

          </li>
        ))}
      </ul>

      <ul role="list" className="space-y-6">
        {activity.map((activityItem, activityItemIdx) => (
          <li key={activityItem.id} className="relative flex gap-x-4">
            <div
              className={classNames(
                activityItemIdx === activity.length - 1 ? 'h-6' : '-bottom-6',
                'absolute left-0 top-0 flex w-6 justify-center'
              )}
            >
              <div className="w-px bg-gray-200" />
            </div>
            {activityItem.type === 'commented' ? (
              <>
                <div className="h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200">
                  <div className="flex justify-between gap-x-4">
                    <div className="py-0.5 text-xs leading-5 text-gray-500">
                      <span className="font-medium text-gray-900">{activityItem.person.name}</span> commented
                    </div>
                    <time dateTime={activityItem.dateTime} className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                      {activityItem.date}
                    </time>
                  </div>
                  <p className="text-sm leading-6 text-gray-500">{activityItem.comment}</p>
                </div>
              </>
            ) : (
              <>
                <div className="relative flex h-6 w-6 flex-none items-center justify-center bg-white">
                  {activityItem.type === 'paid' ? (
                    <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                  ) : (
                    <div className="h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                  )}
                </div>
                <p className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                  <span className="font-medium text-gray-900">{activityItem.person.name}</span> {activityItem.type} the
                  invoice.
                </p>
                <time dateTime={activityItem.dateTime} className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                  {activityItem.date}
                </time>
              </>
            )}
          </li>
        ))}
      </ul>

      <div className="relative py-10">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-white px-2 text-sm text-gray-500">Continue</span>
        </div>
      </div>



      <ul role="list" className="space-y-6">
        {workflowExecution.map((activityItem, activityItemIdx) => (
          <li key={activityItem.id} className="relative flex gap-x-4">
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
                {activityItem.type === 'step' ? (
                  <div className="h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                ) : (
                  <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                )}
              </div>
              <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200">
                <div className="flex justify-between gap-x-4">
                  <div className="py-0.5 text-xs leading-5 text-gray-500">
                    <span className="font-medium text-gray-900">{activityItem.name_for_user}: </span>{activityItem.description_for_user}
                  </div>
                  <time dateTime="2024-04-10" className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                    10 sec.
                  </time>
                </div>
                {
                  activityItem.step_executions.map((stepExecution) => (
                    <>
                      <div className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                        <span className="font-medium text-gray-900">Parameter:</span> {stepExecution.parameters?.toString()}
                      </div>
                      {
                        stepExecution.results.map((resultItem) => (
                          Object.entries(resultItem).map(([key, value]) => (
                            <p className="flex-auto py-0.5 text-xs leading-5 text-gray-500">
                              <span className="font-medium text-gray-900">{key}:</span><br /> {value?.toString()}
                            </p>
                          ))
                        ))
                      }
                    </>
                  ))
                }
              </div>
            </>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default StepProcessDetail;