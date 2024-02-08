import { useMutation } from "@tanstack/react-query";
import { updateCategory } from "services/onboarding";

const useUpdateCategory = () => useMutation(updateCategory);

export default useUpdateCategory;
