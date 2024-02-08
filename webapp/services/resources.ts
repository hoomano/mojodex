import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import {
  GetResourcesResponse,
  RefreshDocumentPayload,
} from "modules/resources/interface";
import { ResourceTab } from "modules/resources";

export const getResources = ({
  queryKey,
  pageParam = 0,
}: any): Promise<GetResourcesResponse> =>
  axiosClient.get(apiRoutes.getResources, {
    params: {
      learned_by_mojo: queryKey?.[1] === ResourceTab.LearnedByMojo,
      n_resources: 10,
      offset: pageParam,
    },
  });

export const deleteResource = (document_pk: number) =>
  axiosClient.delete(apiRoutes.deleteResource, {
    params: { document_pk: document_pk },
  });

export const addDocument = (website_url: string) =>
  axiosClient.put(apiRoutes.addDocument, {
    website_url: website_url,
  });

export const refreshDocument = (payload: RefreshDocumentPayload) =>
  axiosClient.post(apiRoutes.refreshDocument, payload);
