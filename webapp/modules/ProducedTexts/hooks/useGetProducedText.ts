import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getProducedText } from "services/produced_texts";

const useGetDraft = (producedTextPk: number | null, { enabled = true } = {}) =>
  useQuery([cachedAPIName.PRODUCED_TEXT, producedTextPk], getProducedText, {
    enabled: !!producedTextPk && enabled,
  });

export default useGetDraft;
