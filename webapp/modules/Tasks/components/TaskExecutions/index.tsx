import { TaskType } from "modules/Tasks/interface";
import TaskCard from "../TaskCard";
import { useRouter } from "next/router";
import { encryptId } from "helpers/method";

interface TasksTypes {
  tasks: TaskType[];
  isListView?: boolean;
}

const TaskExecutions = ({ tasks, isListView }: TasksTypes) => {
  const router = useRouter();

  const taskCardClickHandler = (task: TaskType) => {
    router.push(`/tasks/${encryptId(task.user_task_execution_pk)}`);
  };

  return (
    <div className={`${isListView ? "" : "flex gap-5 flex-wrap"} mt-2`}>
      {tasks.map((task, index) => {
        return (
          <TaskCard
            title={task.title}
            description={task.summary}
            key={index}
            showActions
            icon={task.icon}
            onClick={() => taskCardClickHandler(task)}
            task={task}
            isListView={isListView}
          />
        );
      })}
    </div>
  );
};

export default TaskExecutions;
