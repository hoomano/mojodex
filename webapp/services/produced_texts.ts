import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import {
  GetAllDraftsResponse,
  GetDraftResponse,
  SaveDraftPayload,
} from "modules/ProducedTexts/interface";

export const deleteDraft = (textPk: number) =>
  axiosClient.delete(apiRoutes.deleteProducedText, {
    params: { produced_text_pk: textPk },
  });

export const saveDraft = (payload: SaveDraftPayload) =>
  axiosClient.post(apiRoutes.saveProducedText, payload);

export const getAllProducedTexts = ({
  pageParam = 0,
}: any): Promise<GetAllDraftsResponse> =>
  axiosClient.get(apiRoutes.producedText, {
    params: { n_produced_texts: 10, offset: pageParam },
  });

export const getProducedText = ({ queryKey }: any): Promise<GetDraftResponse> =>
  axiosClient.get(apiRoutes.producedText, {
    params: { produced_text_pk: queryKey[1] },
  });
