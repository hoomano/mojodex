import React from 'react';

import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import StepProcessDetail from './StepProcessDetail';
import { UserTaskExecution, UserTaskExecutionStepExecution } from 'modules/Tasks/interface';
import { Socket } from 'socket.io-client';


interface WorkflowProps {
    steps: any;
    step_executions: UserTaskExecutionStepExecution[];
}

const Workflow: React.FC<WorkflowProps> = ({ steps, step_executions}) => {

    return (
        <>
            <StepProcessDetail steps={steps} stepExecutions={step_executions} />
            
        </>
    );
};

export default Workflow;
