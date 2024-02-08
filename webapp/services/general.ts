import { apiRoutes } from ".";
import axiosClient from "./config/axiosClient";
import { UpdateSessionResponseType } from "helpers/interface/session";

const updateSession = (body: any): Promise<UpdateSessionResponseType> =>
  axiosClient.put(apiRoutes.updateSession, body);

const acceptTermsAndCondition = (body: any) =>
  axiosClient.put(apiRoutes.acceptTermsAndCondition, body);

export const languageCode = (payload: any) =>
  axiosClient.post(apiRoutes.language, payload);

export const getLanguageCode = (languageCode: string): Promise<any> =>
  axiosClient.get(apiRoutes.language, {
    params: { language_code: languageCode },
  });

export const timezoneSet = (payload: any) =>
  axiosClient.post(apiRoutes.timezone, payload);

export { updateSession, acceptTermsAndCondition };
