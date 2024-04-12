import { useMutation } from "@tanstack/react-query";
import { relaunchStepExecution } from "services/tasks";


const useOnStepExecutionRelaunch = () => useMutation(relaunchStepExecution);

export default useOnStepExecutionRelaunch;
