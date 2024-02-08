import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getAllUserTasks } from "services/tasks";
import { UserTask } from "../interface";

const useGetAllTasks = () =>
  useQuery([cachedAPIName.USER_TASK], getAllUserTasks, {
    staleTime: Infinity,
    select: (data) => {
      const userTasks = data?.user_tasks || [];
      return userTasks as UserTask[];
    },
  });

export default useGetAllTasks;
