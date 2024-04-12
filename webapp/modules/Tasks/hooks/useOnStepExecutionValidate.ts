import { useMutation } from "@tanstack/react-query";
import { validateUserTaskExecutionStepExecution } from "services/tasks";


const useOnStepExecutionValidate = () => useMutation(validateUserTaskExecutionStepExecution);

export default useOnStepExecutionValidate;
