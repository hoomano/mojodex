import { useInfiniteQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getResources } from "services/resources";
import { ResourceTab } from "..";

const useGetResources = (selectedTab: ResourceTab) =>
  useInfiniteQuery([cachedAPIName.RESOURCES, selectedTab], getResources, {
    staleTime: 30 * 1000,
  });

export default useGetResources;
