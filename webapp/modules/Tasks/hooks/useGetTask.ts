import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getTask } from "services/tasks";

const useGetTask = (taskId: number | null) =>
  useQuery([cachedAPIName.USER_TASK, taskId], getTask, { enabled: !!taskId });

export default useGetTask;
