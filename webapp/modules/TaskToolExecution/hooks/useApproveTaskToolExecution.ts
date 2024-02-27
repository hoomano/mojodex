import { useMutation } from "@tanstack/react-query";
import { approveTaskToolExecution } from "services/task_tool_execution";

const useApproveTaskToolExecution = () => useMutation(approveTaskToolExecution);

export default useApproveTaskToolExecution;
