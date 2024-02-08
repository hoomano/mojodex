import { useMutation } from "@tanstack/react-query";
import { acceptTermsAndCondition } from "services/general";

const useAcceptTermAndCondition = () => {
  const mutation = useMutation({
    mutationFn: () =>
      acceptTermsAndCondition({
        datetime: new Date().toISOString(),
      }),
  });

  return mutation;
};

export default useAcceptTermAndCondition;
