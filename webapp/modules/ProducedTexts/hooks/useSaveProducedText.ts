import { useMutation } from "@tanstack/react-query";
import { saveDraft } from "services/produced_texts";

const useSaveDraft = () => useMutation(saveDraft);

export default useSaveDraft;
