import { useMutation } from "@tanstack/react-query";
import { workflowRestart } from "services/tasks";


const useOnWorkflowRestart = () => useMutation(workflowRestart);

export default useOnWorkflowRestart;