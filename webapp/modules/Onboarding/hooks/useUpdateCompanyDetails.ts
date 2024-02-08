import { useMutation } from "@tanstack/react-query";
import { updateCompanyDetails } from "services/onboarding";

const useUpdateCompanyDetails = () => useMutation(updateCompanyDetails);

export default useUpdateCompanyDetails;
