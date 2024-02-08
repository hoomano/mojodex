import { useMutation } from "@tanstack/react-query";
import { deleteUserTaskExecution } from "services/tasks";

const useDeleteUserTaskExecution = () => useMutation(deleteUserTaskExecution)

export default useDeleteUserTaskExecution;