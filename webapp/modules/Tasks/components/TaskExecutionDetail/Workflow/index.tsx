import React from 'react';
import useGetTask from "modules/Tasks/hooks/useGetTask";
import StepProcessDetail from './StepProcessDetail';


interface WorkflowProps {
    taskExecutionPK?: number;
    taskId?: number;
}

const Workflow: React.FC<WorkflowProps> = ({ taskExecutionPK, taskId }) => {

    const { data: task } = useGetTask(taskId ?? null);

    return (


        <StepProcessDetail task={task} taskExecutionPK={taskExecutionPK} />

    );
};

export default Workflow;
