import React from 'react';

import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import StepProcessDetail from './StepProcessDetail';
import { UserTaskExecution } from 'modules/Tasks/interface';


interface WorkflowProps {
    taskExecutionPK?: number;
}

const Workflow: React.FC<WorkflowProps> = ({ taskExecutionPK }) => {
    const { data: currentTask, isLoading } = useGetExecuteTaskById(taskExecutionPK);

    return (
        <>
            {currentTask ? (
                <StepProcessDetail taskExecution={currentTask} />
            ) : (
                <div>Loading...</div>
            )}
        </>
    );
};

export default Workflow;
