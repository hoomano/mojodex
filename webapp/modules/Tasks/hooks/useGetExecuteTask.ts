import { useInfiniteQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getUserTaskExecution } from "services/tasks";

const useGetExecuteTask = (searchFilter: string, userTaskPks: string = "") => {
  return useInfiniteQuery(
    [cachedAPIName.USER_TASK_EXECUTION, searchFilter, userTaskPks],
    ({ pageParam = 0 }) =>
      getUserTaskExecution({
        pageParam,
        searchFilter,
        userTaskPks,
      }),
    {
      staleTime: 30 * 1000,
    }
  );
};

export default useGetExecuteTask;
