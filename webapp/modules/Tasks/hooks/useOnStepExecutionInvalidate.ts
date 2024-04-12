import { useMutation } from "@tanstack/react-query";
import { invalidateUserTaskExecutionStepExecution } from "services/tasks";


const useOnStepExecutionInvalidate = () => useMutation(invalidateUserTaskExecutionStepExecution);

export default useOnStepExecutionInvalidate;
