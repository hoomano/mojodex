import { useSession } from "next-auth/react";
import useGetPurchaseStatus from "./useGetPurchaseStatus";
import { useEffect } from "react";

const useUpdatePurchaseInSession = () => {
  const { data: sessionData, update: updateSession, status } = useSession();
  const getPurchaseStatus = useGetPurchaseStatus();

  useEffect(() => {
    if (
      sessionData &&
      !getPurchaseStatus.data &&
      !getPurchaseStatus.isLoading &&
      status === "authenticated"
    ) {
      getPurchaseStatus.mutate(undefined, {
        onSuccess: (purchaseStatusResponse) => {
          if (sessionData && purchaseStatusResponse?.current_purchases) {
            const updatedSession = {
              ...sessionData,
              authorization: {
                ...(sessionData as any).authorization,
                ...purchaseStatusResponse,
                purchase_status: purchaseStatusResponse.current_purchases.length > 0 ? "active" : "no_purchase"
              },
            };
            updateSession(updatedSession);
          }
        },
      });
    }
  }, [
    getPurchaseStatus.data,
    getPurchaseStatus.isLoading,
    sessionData,
    status,
  ]);

  return null;
};

export default useUpdatePurchaseInSession;
