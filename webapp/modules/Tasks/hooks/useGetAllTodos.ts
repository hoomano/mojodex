import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getAllTodos } from "services/tasks";

const useGetAllTodos = (taskExecutionId?: number) =>
  useQuery([cachedAPIName.TODOS, taskExecutionId], getAllTodos);

export default useGetAllTodos;
