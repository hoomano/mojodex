import { useInfiniteQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getAllProducedTexts } from "services/produced_texts";

const useGetAllProducedTexts = () =>
  useInfiniteQuery([cachedAPIName.PRODUCED_TEXT], getAllProducedTexts, {
    staleTime: 30 * 1000,
  });

export default useGetAllProducedTexts;
