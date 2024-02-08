import { useMutation } from "@tanstack/react-query";
import { deleteTodo } from "services/tasks";

const useDeleteTodo = () => useMutation(deleteTodo);

export default useDeleteTodo;
