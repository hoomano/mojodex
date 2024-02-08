import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getDraft } from "services/drafts";

const useGetDraft = (draftPk: number | null, { enabled = true } = {}) =>
  useQuery([cachedAPIName.DRAFTS, draftPk], getDraft, {
    enabled: !!draftPk && enabled,
  });

export default useGetDraft;
