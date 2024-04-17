import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import {
  UpdateCompanyDetailsPayload,
  BusinessGoal,
  ProfileCategoryAPIResponse
} from "modules/Onboarding/interface";

export const registerCompany = (companyUrl: string) =>
  axiosClient.put(apiRoutes.registerCompany, { website_url: companyUrl });

export const updateCompanyDetails = (payload: UpdateCompanyDetailsPayload) =>
  axiosClient.post(apiRoutes.updateCompanyDetails, payload);

export const updateBusinessGoal = (payload: BusinessGoal) =>
  axiosClient.put(apiRoutes.goal, payload);

export const getProfileCategories = (): Promise<ProfileCategoryAPIResponse> =>
  axiosClient.get(apiRoutes.profileCategories);

export const updateCategory = (profile_category_pk: number) =>
  axiosClient.put(apiRoutes.updateProfileCategory, { "profile_category_pk": profile_category_pk});

export const onboardingPresentedSet = (): Promise<any> =>
  axiosClient.put(apiRoutes.onboardingPresented);
