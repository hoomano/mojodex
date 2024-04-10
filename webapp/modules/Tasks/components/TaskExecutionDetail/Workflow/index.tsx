import React from 'react';

import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import StepProcessDetail from './StepProcessDetail';
import { UserTaskExecution } from 'modules/Tasks/interface';


interface WorkflowProps {
    currentTask: UserTaskExecution;
}

const Workflow: React.FC<WorkflowProps> = ({ currentTask }) => {

    return (
        <>
             <StepProcessDetail taskExecution={currentTask} />
            
        </>
    );
};

export default Workflow;
