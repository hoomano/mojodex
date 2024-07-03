import React, { createContext, useState, ReactNode } from "react";
import { UserTaskExecution } from "modules/Tasks/interface";

interface TaskContextType {
    tasks: UserTaskExecution[];
    setTasks: React.Dispatch<React.SetStateAction<UserTaskExecution[]>>;
    updateTask: (updatedTask: UserTaskExecution) => void;
}

export const TaskContext = createContext<TaskContextType | undefined>(undefined);

interface TaskProviderProps {
    children: ReactNode;
}

const TaskProvider = ({ children }: TaskProviderProps) => {
    const [tasks, setTasks] = useState<UserTaskExecution[]>([]);

    const updateTask = (updatedTask: UserTaskExecution) => {
        console.log("ici")
        setTasks((prevTasks) =>
            prevTasks.map((task) =>
                task.user_task_execution_pk === updatedTask.user_task_execution_pk ? updatedTask : task
            )
        );
        console.log(updatedTask.title);
    };

    return (
        <TaskContext.Provider value={{ tasks, setTasks, updateTask }}>
            {children}
        </TaskContext.Provider>
    );
};

export default TaskProvider;