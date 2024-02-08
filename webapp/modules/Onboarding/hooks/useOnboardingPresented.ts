import { useMutation } from "@tanstack/react-query";
import { onboardingPresentedSet } from "services/onboarding";

const useOnboardingPresented = () => useMutation(onboardingPresentedSet);

export default useOnboardingPresented;
