import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getExecuteTaskById } from "services/tasks";

const useGetExecuteTaskById = (taskId?: number | null, options: any = {}) =>
  useQuery([cachedAPIName.GET_EXECUTE_TASK_BY_ID, taskId], getExecuteTaskById, {
    ...options,
  });

export default useGetExecuteTaskById;
