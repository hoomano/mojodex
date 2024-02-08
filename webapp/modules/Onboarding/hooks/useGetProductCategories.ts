import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getProductCategories } from "services/onboarding";

const useGetProductCategories = () =>
    useQuery([cachedAPIName.PRODUCT_CATEGORIES], getProductCategories);

export default useGetProductCategories;

