
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";
import useOnStepExecutionRelaunch from "modules/Tasks/hooks/useOnStepExecutionRelaunch";
import { useTranslation } from "next-i18next";
import { useState } from "react";
import Step from "./Step";
import { on } from "events";



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




  return (
    <div className="p-[60px] w-full">
      <ul role="list" className="space-y-6 w-full">
        {stepExecutions?.map((stepItem, stepItemIdx) => (
          <Step
            stepExecution={stepItem}
            onInvalidate={onInvalidate}
            onValidate={onValidate}
            onStepRelaunched={onStepRelaunched}
          />
        ))}
      </ul>

    </div>
  );
};

export default StepProcessDetail;