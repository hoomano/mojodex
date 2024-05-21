import { useEffect, useMemo, useState } from "react";
import Loader from "components/Loader";
import useGetAllTodos from "modules/Tasks/hooks/useGetAllTodos";
import moment from "moment";
import { Todos } from "modules/Tasks/interface/todos";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCommentDots,
  faSquareCheck,
  faTrash,
  faBan,
} from "@fortawesome/free-solid-svg-icons";
import useDeleteTodo from "modules/Tasks/hooks/useDeleteTodo";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import useOnTodoComplete from "modules/Tasks/hooks/useOnTodoComplete";
import { formatDateString } from "./FormatDate";
import { useTranslation } from "react-i18next";

interface TodosType {
  taskExecutionPK: number;
  workingOnTodos: boolean | undefined;
  nTodos: number | undefined;
}

const TodosView = ({ taskExecutionPK, workingOnTodos, nTodos }: TodosType) => {
  const [todoCompletionStates, setTodoCompletionStates] = useState<{
    [key: number]: boolean;
  }>({});
  const { data, isLoading } = useGetAllTodos(taskExecutionPK);
  const onTodoComplete = useOnTodoComplete();
  const deleteTodo = useDeleteTodo();
  const { showAlert } = useAlert();
  const { t } = useTranslation("dynamic");

  const [showUnreadTodo, setShowUnreadTodo] = useState(false);

  useEffect(() => {
    if (data?.n_todos_not_read) {
      if (!showUnreadTodo) setShowUnreadTodo(true);
      handleTodoMarkAsRead();
    }
  }, [data]);

  const handleTodoMarkAsRead = () => {
    onTodoComplete.mutate({
      datetime: new Date().toISOString(),
      user_task_execution_pk: taskExecutionPK,
      mark_as_read: true,
      mark_as_done: false,
    });
    invalidateQuery([cachedAPIName.USER_TASK_EXECUTION]);
  };

  const onDeleteTodo = (todoPk: number) => {
    deleteTodo.mutate(todoPk, {
      onSuccess: () => {
        showAlert({
          title: "Todo deleted successfully.",
          type: "success",
        });
        invalidateQuery([cachedAPIName.TODOS]);
      },
      onError: (error: any) => {
        showAlert({
          title: error,
          type: "error",
        });
      },
    });
  };

  const taskCompleteClickHandler = (todo: Todos) => {
    const { todo_pk, user_task_execution_fk, completed } = todo;

    if (completed) {
      return;
    }

    const updatedStates = { ...todoCompletionStates };
    updatedStates[todo_pk] = !updatedStates[todo_pk];
    setTodoCompletionStates(updatedStates);

    onTodoComplete.mutate(
      {
        datetime: new Date().toISOString(),
        user_task_execution_pk: user_task_execution_fk,
        todo_pk: todo_pk,
        mark_as_read: !updatedStates[todo_pk],
        mark_as_done: updatedStates[todo_pk],
      },
      {
        onSuccess: () => { },
      }
    );
  };

  const groupedTodos = useMemo(() => {
    const result: any = {};

    data?.todos.forEach((todo: any) => {
      // const formattedDate = moment(todo.scheduled_date).format("DD MMM YYYY");
      const formattedDate: any = formatDateString(todo.scheduled_date);

      if (!result[formattedDate]) {
        result[formattedDate] = [];
      }

      result[formattedDate].push(todo);
    });

    return result;
  }, [data]);

  return (
    <div className="py-3">
      {isLoading && <Loader />}

      {!isLoading && workingOnTodos == true && (
        <div className="flex justify-center items-center h-[calc(100vh-260px)] m-auto text-xl">
          <div>
            {t("userTaskExecution.todosTab.workingOnTodosEmoji")}
            <div className="my-2">
              {t("userTaskExecution.todosTab.workingOnTodosTitleMessage")}
            </div>
            <div className="text-gray-lighter">
              {t("userTaskExecution.todosTab.workingOnTodosBodyMessage")}
            </div>
          </div>
        </div>
      )}

      {!isLoading && workingOnTodos == false && nTodos == 0 && (
        <div className="flex justify-center items-center h-[calc(100vh-260px)] m-auto text-xl">
          <div>
            {t("userTaskExecution.todosTab.notWorkingOnTodosEmoji")}
            <div>
              {t("userTaskExecution.todosTab.notWorkingOnTodosTitleMessage")}
            </div>
          </div>
        </div>
      )}

      {Object.keys(groupedTodos).map((scheduledDate) => (
        <div key={scheduledDate}>
          <h2 className="text-gray-400 my-2.5">{scheduledDate}</h2>
          {groupedTodos[scheduledDate].map((todo: Todos) => (
            <div className="flex items-center gap-6 py-3" key={todo.todo_pk}>
              {showUnreadTodo && todo.read_by_user === null ? (
                <div className="h-2 w-2 rounded-full bg-blue-600"></div>
              ) : (
                <div className="w-2 h-2"></div>
              )}

              {todo.completed == null &&
                moment(todo.scheduled_date).isBefore(moment(), "day") ? (
                <FontAwesomeIcon
                  icon={faBan}
                  className="text-gray-lighter w-5 h-5"
                />
              ) : (
                <input
                  type="checkbox"
                  className="w-5 h-5 rounded-full text-[#869CB4] focus:ring-0 focus:ring-offset-0"
                  onChange={() => taskCompleteClickHandler(todo)}
                  checked={
                    !!todo.completed || todoCompletionStates[todo.todo_pk]
                  }
                />
              )}
              <div className="flex-1">
                <div
                  className={`text-[14px] ${!!todo.completed || todoCompletionStates[todo.todo_pk]
                      ? "line-through italic"
                      : ""
                    }`}
                >
                  {todo.description}
                </div>
              </div>
              <FontAwesomeIcon
                icon={faTrash}
                className="text-gray-lighter text-xs cursor-pointer"
                onClick={() => onDeleteTodo(todo?.todo_pk)}
              />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default TodosView;
