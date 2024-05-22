import { useEffect, useMemo, useState } from "react";
import Loader from "components/Loader";
import useGetAllTodos from "modules/Tasks/hooks/useGetAllTodos";
import moment from "moment";
import { useRouter } from "next/router";
import { encryptId } from "helpers/method";
import { Todos } from "modules/Tasks/interface/todos";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTrash, faBan } from "@fortawesome/free-solid-svg-icons";
import useDeleteTodo from "modules/Tasks/hooks/useDeleteTodo";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import useOnTodoComplete from "modules/Tasks/hooks/useOnTodoComplete";
import { formatDateString } from "modules/Tasks/components/TaskExecutionDetail/Todos/FormatDate";

const TodosDrawer = () => {
  const [todoCompletionStates, setTodoCompletionStates] = useState<{
    [key: number]: boolean;
  }>({});
  const { data, isLoading } = useGetAllTodos();
  const onTodoComplete = useOnTodoComplete();
  const router = useRouter();
  const deleteTodo = useDeleteTodo();
  const { showAlert } = useAlert();

  const [showUnreadTodo, setShowUnreadTodo] = useState(false);

  useEffect(() => {
    if (data?.n_todos_not_read && !showUnreadTodo) setShowUnreadTodo(true);
  }, [data]);

  const handleTodoMarkAsRead = () => {
    if (data?.n_todos_not_read) {
      onTodoComplete.mutate({
        datetime: new Date().toISOString(),
        mark_as_read: true,
        mark_as_done: false,
      });
      invalidateQuery([cachedAPIName.USER_TASK_EXECUTION]);
    }
  };

  useEffect(() => {
    handleTodoMarkAsRead();
  }, [data]);

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
      const formattedDate = formatDateString(todo.scheduled_date);

      if (!result[formattedDate]) {
        result[formattedDate] = [];
      }

      result[formattedDate].push(todo);
    });

    return result;
  }, [data]);

  const todoClickHandler = (todo: Todos) => {
    invalidateQuery([cachedAPIName.TODOS]);
    router.push(`/tasks/${encryptId(todo.user_task_execution_fk)}?tab=todos`);
  };

  return (
    <div className="p-4 md:p-14">
      {isLoading && <Loader />}

      {!isLoading && !data?.todos?.length && (
        <>
          <div className="text-h3 font-semibold">🎉</div>
          <div className="text-h3 font-semibold">
            Great job! To-do list empty.
          </div>
        </>
      )}

      {Object.keys(groupedTodos).map((formattedDate) => (
        <div key={formattedDate}>
          <h2
            className={`text-gray-400 my-2.5 ${formattedDate === "Today" && "text-2xl !text-black font-bold"
              }`}
          >
            {formattedDate}
          </h2>
          {groupedTodos[formattedDate].map((todo: Todos) => (
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
                  className={`text-[14px] cursor-pointer ${!!todo.completed || todoCompletionStates[todo.todo_pk]
                      ? "line-through italic"
                      : ""
                    }`}
                  onClick={() => todoClickHandler(todo)}
                >
                  {todo.description}
                </div>
              </div>
              <FontAwesomeIcon
                icon={faTrash}
                className="ml-10 text-gray-lighter text-xs cursor-pointer mr-5"
                onClick={() => onDeleteTodo(todo?.todo_pk)}
              />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default TodosDrawer;
