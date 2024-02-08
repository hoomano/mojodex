import { useMutation } from "@tanstack/react-query";
import { saveDraft } from "services/drafts";

const useSaveDraft = () => useMutation(saveDraft);

export default useSaveDraft;
