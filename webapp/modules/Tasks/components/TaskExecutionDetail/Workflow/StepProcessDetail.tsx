
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import { useRouter } from "next/router";
import { useState, useEffect } from "react";
import Button from "components/Button";
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";
import useOnStepExecutionRelaunch from "modules/Tasks/hooks/useOnStepExecutionRelaunch";

import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid'
import BeatLoader from "react-spinners/BeatLoader";
import { useTranslation } from "next-i18next";


function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface StepProcessDetailProps {
  stepExecutions: UserTaskExecutionStepExecution[];
  onInvalidate: any;
  onValidate: any;
  onStepRelaunched: any;
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  stepExecutions,
  onInvalidate,
  onValidate,
  onStepRelaunched
}) => {
  const { t } = useTranslation('dynamic');
  const onValidateStepExecution = useOnStepExecutionValidate();
  const onInvalidateStepExecution = useOnStepExecutionInvalidate();
  const onStepExecutionRelaunch = useOnStepExecutionRelaunch();

  const calculateTimeAgo = (creationDate: string) => {
    const providedDate: any = new Date(creationDate);
    const currentDate: any = new Date();
    const timeDifference = currentDate - providedDate;

    // Calculate minutes, hours, and days
    const minutes = Math.floor(timeDifference / (1000 * 60));
    const hours = Math.floor(timeDifference / (1000 * 60 * 60));
    const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));

    let time_ago;

    if (minutes < 1) {
      time_ago = "now";
    } else if (hours < 1) {
      time_ago = `${minutes}min ago`;
    } else if (days < 1) {
      time_ago = `${hours}h ago`;
    } else if (days <= 7) {
      const dayOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][providedDate.getDay()];
      const timeString = `${dayOfWeek} ${providedDate.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
      time_ago = timeString;
    } else {
      time_ago = providedDate.toISOString().slice(0, 10);
    }

    return time_ago;
  };

  const onReviewStep = (user_workflow_step_execution_pk: number) => {
    onInvalidateStepExecution.mutate(user_workflow_step_execution_pk, {
      onSuccess: () => {
        onInvalidate();
      },
      onError: (error) => {
        console.log("Error invalidating step", error);
      }
    }
    );
  };

  const onRelaunchStep = (user_workflow_step_execution_pk: number) => {
    onStepExecutionRelaunch.mutate(user_workflow_step_execution_pk, {
      onSuccess: () => {
        onStepRelaunched(user_workflow_step_execution_pk);
      },
      onError: (error) => {
        console.log("Error relaunching step", error);
      }
    }
    );
  };

  const onContinueStep = (user_workflow_step_execution_pk: number) => {
    onValidateStepExecution.mutate(user_workflow_step_execution_pk, {
      onSuccess: () => {
        onValidate(user_workflow_step_execution_pk);
      },
      onError: (error) => {
        console.log("Error validating step", error);
      }
    }
    );
  };

  return (
    <div className="p-[60px] w-full">
      <div>
        <div className="text-h4 font-semibold text-gray-darker pb-4">
          Workflow
        </div>

      </div>

      <ul role="list" className="space-y-6 w-full">
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
              <div className="flex flex-row w-full">
                <div className="relative h-6 w-6 flex-none items-center justify-center bg-white">
                  {stepItem.validated === true ? (
                    <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                  ) : stepItem.error_status != null ? (
                    <ExclamationCircleIcon className="h-6 w-6 text-red-500" aria-hidden="true" />
                  ) : (
                    <div className="mt-1.5 ml-2 h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                  )}
                </div>
                <div className="flex-col pl-3 w-full">
                  <div className="flex justify-between gap-x-4">
                    <div className="py-0.5 text-sm leading-5 text-gray-500">
                      {stepItem.step_name_for_user}: <span className="font-medium text-gray-900">{stepItem.step_definition_for_user}</span>
                    </div>
                    <time dateTime={stepItem.creation_date} className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                      {calculateTimeAgo(stepItem.creation_date)}
                    </time>
                  </div>
                  <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200 w-full">

                    {
                      Object.entries(stepItem.parameter).map(([key, value]) => (
                        <p className="flex-auto text-xs leading-5 text-gray-500 italic">
                          <span className="font-medium text-gray-400">{t("userTaskExecution.processTab.stepExecutionParameters")}:</span><br />
                          {key}: {value?.toString()}
                        </p>
                      ))
                    }
                    {
                      stepItem.result != null && stepItem.result.length > 0 ?
                        <div className="relative">
                          <div className="absolute inset-0 flex items-center" aria-hidden="true">
                            <div className="w-full border-t border-gray-300" />
                          </div>
                          <div className="relative flex justify-center">
                            <span className="bg-white px-2 text-xs text-gray-400">{t("userTaskExecution.processTab.stepExecutionResults")}</span>
                          </div>
                        </div> : (stepItem.error_status === null ? <BeatLoader color="#3763E7" /> :
                          <div className="relative">
                            <p className="text-primary-main text-sm leading-5"> {t("userTaskExecution.processTab.stepExecutionError")}</p>
                            <p className="text-gray-dark text-sm leading-5">{t("userTaskExecution.processTab.stepExecutionErrorInstruction")}</p>
                          </div>
                        )
                    }
                    {
                      // we want to iterate on each result that is a JSON object and display key value pairs
                      stepItem.result?.map((resultItem) => (
                        Object.entries(resultItem).map(([key, value]) => (
                          <p className="flex-auto py-0.5 text-sm leading-5 text-gray-900">
                            <span className="font-medium text-gray-400">{key}:</span><br /> {value?.toString()}
                          </p>
                        ))
                      ))
                    }
                    {stepItem.validated === null && stepItem.result != null ?
                      <div className="text-end pt-2">
                        <Button
                          variant="outline"
                          size="middle"
                          onClick={() => onReviewStep(stepItem.user_workflow_step_execution_pk)}
                          className="mr-2"
                        >
                          {t("userTaskExecution.processTab.invalidateButton")}
                        </Button>

                        <Button variant="primary" size="middle" onClick={() => onContinueStep(stepItem.user_workflow_step_execution_pk)}>
                          {t("userTaskExecution.processTab.validateButton")}
                        </Button>
                      </div> : null
                    }
                    {stepItem.error_status != null ?
                      <div className="text-end pt-2">
                        <Button
                          variant="outline"
                          size="middle"
                          onClick={() => onRelaunchStep(stepItem.user_workflow_step_execution_pk)}
                          className="mr-2"
                        >
                          {t("userTaskExecution.processTab.relaunchButton")}
                        </Button>
                      </div> : null
                    }
                  </div>
                </div>
              </div>
            </>

          </li>
        ))}
      </ul>

    </div>
  );
};

export default StepProcessDetail;