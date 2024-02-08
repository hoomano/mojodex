import { useMutation } from "@tanstack/react-query";
import { updateBusinessGoal } from "services/onboarding";

const useUpdateBusinessGoal = () => useMutation(updateBusinessGoal);

export default useUpdateBusinessGoal;
