import { useMutation } from "@tanstack/react-query";
import { onTaskComplete } from "services/tasks";

const useOnTaskComplete = () => useMutation(onTaskComplete);

export default useOnTaskComplete;
