import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import {
  GetAllDraftsResponse,
  GetDraftResponse,
  SaveDraftPayload,
} from "modules/Drafts/interface";

export const deleteDraft = (textPk: number) =>
  axiosClient.delete(apiRoutes.deleteDraft, {
    params: { produced_text_pk: textPk },
  });

export const saveDraft = (payload: SaveDraftPayload) =>
  axiosClient.post(apiRoutes.saveDraft, payload);

export const getAllDrafts = ({
  pageParam = 0,
}: any): Promise<GetAllDraftsResponse> =>
  axiosClient.get(apiRoutes.drafts, {
    params: { n_produced_texts: 10, offset: pageParam },
  });

export const getDraft = ({ queryKey }: any): Promise<GetDraftResponse> =>
  axiosClient.get(apiRoutes.drafts, {
    params: { produced_text_pk: queryKey[1] },
  });
