import { useMutation, useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getLanguageCode } from "services/general";

const useGetLanguageCode = (
  languageCode: string | null | undefined,
  { enabled = true } = {}
) =>
  useQuery(
    [cachedAPIName.LANGUAGE, languageCode],
    () => languageCode && getLanguageCode(languageCode),
    {
      enabled: !!languageCode && enabled,
    }
  );

export default useGetLanguageCode;

export const useGetLanguageCodeMutation = () => useMutation(getLanguageCode);
