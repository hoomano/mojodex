import { useMutation } from "@tanstack/react-query";
import { executeTask } from "services/tasks";

const usePostExecuteTask = () => useMutation(executeTask);

export default usePostExecuteTask;
