import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";

import {
  PurchaseStatusResponse,
  StripeCheckoutSessionResponse,
} from "helpers/interface/alltypes";

export const createStripeCheckoutSession = (params: {
  productStripeId: string;
  isSubscribeType: boolean;
}): Promise<StripeCheckoutSessionResponse> =>
  axiosClient.get(apiRoutes.createStripeCheckoutSession, {
    params,
  });

export const getPurchaseStatus = (): Promise<PurchaseStatusResponse> =>
  axiosClient.get(apiRoutes.purchaseStatus);
