import { useContext, useEffect, useState } from "react";
import {
  FunnelIcon,
  Bars3Icon,
  Squares2X2Icon,
} from "@heroicons/react/24/outline";
import Button from "components/Button";
import EmptyState from "./components/EmptyState";
import TaskListModal from "./components/TaskListModal";
import useGetAllTasks from "./hooks/useGetAllTasks";
import useGetExecuteTask from "./hooks/useGetExecuteTask";
import ProactiveFollowup from "./components/TaskExecutions";
import Loader from "components/Loader";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import TaskDoneModal from "./components/TaskDoneModal";
import { debounce } from "helpers/method";
import { useTranslation } from "react-i18next";
import { useDebounce } from "use-debounce";
import { UserTaskExecution, UserTask } from "./interface";
import { TaskContext } from "./helpers/TaskContext";
import TaskExecutions from "./components/TaskExecutions";

const Tasks = () => {
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [searchTask, setSearchTask] = useState("");
  const [userTasksSuggestions, setUserTasksSuggestions] = useState<number[]>([]);
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  const [isListView, setIsListView] = useState(false);
  const { data: taskList } = useGetAllTasks();
  const { t } = useTranslation("dynamic");
  const [searchInput] = useDebounce(searchTask, 500);

  const {
    fetchNextPage,
    data: executeTasks,
    isLoading,
    isFetching,
  } = useGetExecuteTask(searchInput, userTasksSuggestions.join(";"));

  const { globalState, setGlobalState } = useContext(
    globalContext
  ) as GlobalContextType;

  const taskContext = useContext(TaskContext);

  if (!taskContext) {
    throw new Error("Tasks must be used within a TaskProvider");
  }

  const { tasks, setTasks } = taskContext;

  const startANewTaskHandler = () => {
    setIsTaskModalOpen(true);
  };

  useEffect(() => {
    setTasks(
      executeTasks?.pages?.flatMap((data) => data.user_task_executions) || []
    );
  }, [executeTasks, setTasks]);



  const userTaskExecutionExists = !!tasks?.length;

  const handleRefetchOnScrollEnd = async (e: any) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (!isFetching && scrollHeight - scrollTop <= clientHeight * 1.2) {
      await fetchNextPage({ pageParam: tasks.length });
    }
  };

  const suggestionsClickHandler = (userTaskPk: number) => {
    if (userTasksSuggestions.includes(userTaskPk)) {
      const filterUserTasks = userTasksSuggestions.filter(
        (el: number) => el !== userTaskPk
      );
      setUserTasksSuggestions(filterUserTasks);
    } else {
      setUserTasksSuggestions([...userTasksSuggestions, userTaskPk]);
    }
  };

  const toggleFilterPanel = () => {
    setIsFilterPanelOpen(!isFilterPanelOpen);
  };

  const isShowSearchFilter =
    userTaskExecutionExists ||
    !!searchInput.length ||
    !!userTasksSuggestions.length;

  return (
    <div
      className="h-[calc(100vh-72px)] lg:h-screen grow bg-white overflow-auto p-[30px] sm:p-[60px]"
      onScroll={debounce(handleRefetchOnScrollEnd)}
    >
      <div className="flex justify-between mb-[30px]">
        <div className="text-h2">{t("appDrawer.taskListButton")}</div>
        {userTaskExecutionExists && (
          <Button
            onClick={startANewTaskHandler}
            size="middle"
            className="h-1/4"
          >
            {t("appDrawer.newTaskButton")}
          </Button>
        )}
      </div>
      {isShowSearchFilter && (
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder={t("userTaskExecutionList.searchTaskPlaceholder")}
              className="rounded-md"
              value={searchTask}
              onChange={(e) => {
                setSearchTask(e.target.value);
              }}
            />
            <FunnelIcon
              className={`h-6 w-6 cursor-pointer ${userTasksSuggestions.length
                ? "text-primary-main"
                : "text-gray-lighter"
                }`}
              aria-hidden="true"
              onClick={toggleFilterPanel}
            />
          </div>
          <div className="flex items-center border border-gray-lighter rounded-md">
            <div
              className={`cursor-pointer border-r border-gray-lighter py-1 px-2 ${isListView ? "text-primary-main" : "text-gray-lighter"
                }`}
              onClick={() => setIsListView(true)}
            >
              <Bars3Icon className="h-6 w-6" />
            </div>
            <div
              className={`cursor-pointer py-1 px-2 ${!isListView ? "text-primary-main" : "text-gray-lighter"
                }`}
              onClick={() => setIsListView(false)}
            >
              <Squares2X2Icon className="h-5 w-5" />
            </div>
          </div>
        </div>
      )}

      {isFilterPanelOpen && isShowSearchFilter && (
        <div>
          {taskList?.map((result: UserTask) => (
            <button
              key={result.user_task_pk}
              className={`${userTasksSuggestions.includes(result.user_task_pk!)
                ? "bg-primary-main text-white"
                : ""
                } ml-2 my-2 text-subtitle5 font-semibold text-primary-main border-primary-main border py-1.5 px-4 rounded-full`}
              onClick={() => suggestionsClickHandler(result.user_task_pk!)}
            >
              {result.task_icon} {result.task_name}
            </button>
          ))}
        </div>
      )}

      {userTaskExecutionExists ? (
        <TaskExecutions tasks={tasks} isListView={isListView} />
      ) : isLoading ? (
        <Loader />
      ) : (
        <EmptyState
          startANewTaskHandler={startANewTaskHandler}
          searchInput={searchInput}
          userTaskExecutionsExist={userTaskExecutionExists}
          userTasksSuggestions={userTasksSuggestions}
        />
      )}
      <TaskListModal
        isOpen={isTaskModalOpen}
        tasks={taskList}
        closed={() => setIsTaskModalOpen(false)}
      />
      <TaskDoneModal
        isOpen={!!globalState.showTaskDoneModal}
        closed={() => setGlobalState({ showTaskDoneModal: false })}
      />

      {isFetching && userTaskExecutionExists && (
        <div className="button-loader m-auto !w-10 !h-10 mt-5" />
      )}
    </div>
  );
};

export default Tasks;