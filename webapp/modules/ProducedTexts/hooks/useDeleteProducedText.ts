import { useMutation } from "@tanstack/react-query";
import { deleteDraft as deleteProducedText } from "services/produced_texts";

const useDeleteProducedText = () => useMutation(deleteProducedText);

export default useDeleteProducedText;
