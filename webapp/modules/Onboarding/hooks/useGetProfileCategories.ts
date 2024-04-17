import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getProfileCategories } from "services/onboarding";

const useGetProfileCategories = () =>
    useQuery([cachedAPIName.PROFILE_CATEGORIES], getProfileCategories);

export default useGetProfileCategories;

