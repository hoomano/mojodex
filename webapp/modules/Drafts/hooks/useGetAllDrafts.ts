import { useInfiniteQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getAllDrafts } from "services/drafts";

const useGetAllDrafts = () =>
  useInfiniteQuery([cachedAPIName.DRAFTS], getAllDrafts, {
    staleTime: 30 * 1000,
  });

export default useGetAllDrafts;
