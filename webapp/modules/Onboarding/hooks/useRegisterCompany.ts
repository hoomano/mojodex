import { useMutation } from "@tanstack/react-query";
import { registerCompany } from "services/onboarding";

const useRegisterCompany = () => useMutation(registerCompany);

export default useRegisterCompany;
