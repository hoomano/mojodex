
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import Step from "./Step";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface StepProcessDetailProps {
  stepExecutions: UserTaskExecutionStepExecution[];
  onInvalidate: any;
  onValidate: any;
  onStepRelaunched: any;
  onRestartWorkflow: any;
}

const StepProcessDetail: React.FC<StepProcessDetailProps> = ({
  stepExecutions,
  onInvalidate,
  onValidate,
  onStepRelaunched,
  onRestartWorkflow,
}) => {

  return (
    <div className="p-[60px] w-full">
      <ul role="list" className="space-y-6 w-full">
        {stepExecutions?.map((stepItem, stepItemIdx) => (
          <li key={stepItem.user_workflow_step_execution_pk} className="relative flex gap-x-4">
            <div
              className={classNames(
                stepItemIdx === stepExecutions.length - 1 ? 'h-6' : '-bottom-6',
                'absolute left-0 top-0 flex w-6 justify-center'
              )}
            >
              <div className="w-px bg-gray-200" />
            </div>
          
          <Step
            stepExecution={stepItem}
            onInvalidate={onInvalidate}
            onValidate={onValidate}
              onStepRelaunched={onStepRelaunched}
              isFirstStep={stepItemIdx === 0}
              onRestart={onRestartWorkflow}
            />
          </li>
        ))}
      </ul>

    </div>
  );
};

export default StepProcessDetail;