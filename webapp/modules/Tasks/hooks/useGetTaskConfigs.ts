import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getTaskConfigs } from "services/tasks";

const useGetTaskConfigs = (taskPk?: number | null) =>
  useQuery([cachedAPIName.TASK_CONFIGS, taskPk], getTaskConfigs, {
    enabled: !!taskPk,
    staleTime: 0,
  });

export default useGetTaskConfigs;
