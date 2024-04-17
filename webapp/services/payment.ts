import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";

import {
  RoleStatusResponse,
  StripeCheckoutSessionResponse,
} from "helpers/interface/alltypes";

export const createStripeCheckoutSession = (params: {
  productStripeId: string;
  isSubscribeType: boolean;
}): Promise<StripeCheckoutSessionResponse> =>
  axiosClient.get(apiRoutes.createStripeCheckoutSession, {
    params,
  });

export const getRoleStatus = (): Promise<RoleStatusResponse> =>
  axiosClient.get(apiRoutes.roleStatus);
