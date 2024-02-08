import { useMutation } from "@tanstack/react-query";
import { deleteDraft } from "services/drafts";

const useDeleteDraft = () => useMutation(deleteDraft);

export default useDeleteDraft;
