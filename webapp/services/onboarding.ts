import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import {
  UpdateCompanyDetailsPayload,
  BusinessGoal,
  ProductCategoryAPIResponse
} from "modules/Onboarding/interface";

export const registerCompany = (companyUrl: string) =>
  axiosClient.put(apiRoutes.registerCompany, { website_url: companyUrl });

export const updateCompanyDetails = (payload: UpdateCompanyDetailsPayload) =>
  axiosClient.post(apiRoutes.updateCompanyDetails, payload);

export const updateBusinessGoal = (payload: BusinessGoal) =>
  axiosClient.put(apiRoutes.goal, payload);

export const getProductCategories = (): Promise<ProductCategoryAPIResponse> =>
  axiosClient.get(apiRoutes.productCategories);

export const updateCategory = (product_category_pk: number) =>
  axiosClient.put(apiRoutes.updateProductCategory, { "product_category_pk": product_category_pk});

export const onboardingPresentedSet = (): Promise<any> =>
  axiosClient.put(apiRoutes.onboardingPresented);
