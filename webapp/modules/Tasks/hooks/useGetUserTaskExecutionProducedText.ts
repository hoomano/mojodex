import { useQuery } from "@tanstack/react-query";
import { getUserTaskExecutionProducedText } from "services/tasks";


const useGetUserTaskExecutionProducedText = (producedTextIndex: number, userTaskExecutionPk: number) => useQuery(
    ["getUserTaskExecutionProducedText", producedTextIndex, userTaskExecutionPk],
    () => getUserTaskExecutionProducedText(producedTextIndex, userTaskExecutionPk),
    {
        enabled: producedTextIndex !== null && userTaskExecutionPk !== null,
    }
    );

export default useGetUserTaskExecutionProducedText;
