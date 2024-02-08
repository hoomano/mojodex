import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";

export const forgotPassword = (email: string) =>
  axiosClient.put(apiRoutes.forgotPassword, { email });

export const resetPassword = (payload: {
  Authorization: string;
  new_password: string;
}) => axiosClient.post(apiRoutes.resetPassword, payload);
