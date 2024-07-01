import { useMutation } from "@tanstack/react-query";
import { saveTaskExecutionTitle } from "services/tasks";


const useOnSaveTaskExecutionTitle = () => useMutation(saveTaskExecutionTitle);

export default useOnSaveTaskExecutionTitle;