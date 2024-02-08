import { useMutation } from "@tanstack/react-query";
import { onTodoComplete } from "services/tasks";

const useOnTodoComplete = () => useMutation(onTodoComplete);

export default useOnTodoComplete;
