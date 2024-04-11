
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import { useRouter } from "next/router";
import { useState, useEffect } from "react";
import Button from "components/Button";
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";


import { CheckCircleIcon } from '@heroicons/react/24/solid'
import BeatLoader from "react-spinners/BeatLoader";


function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface StepProcessDetailProps {
  stepExecutions: UserTaskExecutionStepExecution[];
  onInvalidate: any;
  onValidate: any;
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  stepExecutions,
  onInvalidate,
  onValidate,
}) => {

  const onValidateStepExecution = useOnStepExecutionValidate();
  const onInvalidateStepExecution = useOnStepExecutionInvalidate();



  const onUndoStep = () => {
    //event.stopPropagation();
    onInvalidate();
  };

  const onContinueStep = (user_workflow_step_execution_pk: number) => {
    //event.stopPropagation();
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
              <div className="flex flex-row">
                <div className="relative h-6 w-6 flex-none items-center justify-center bg-white">
                  {stepItem.validated === true ? (
                    <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                  ) : (
                    <div className="mt-1.5 ml-2 h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                  )}
                </div>
                <div className="flex-col pl-3">
                  <div className="flex justify-between gap-x-4">
                    <div className="py-0.5 text-sm leading-5 text-gray-500">
                     {stepItem.step_name_for_user}: <span className="font-medium text-gray-900">{stepItem.step_definition_for_user}</span>
                    </div>
                    <time dateTime="2024-04-10" className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                      TODO date
                    </time>
                  </div>
                  <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200">

                    {
                      Object.entries(stepItem.parameter).map(([key, value]) => (
                        <p className="flex-auto text-xs leading-5 text-gray-500 italic">
                          <span className="font-medium text-gray-400">Parameters:</span><br />
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
                            <span className="bg-white px-2 text-xs text-gray-400">Results</span>
                          </div>
                        </div> : <BeatLoader color="#3763E7" />
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