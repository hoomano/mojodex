import useStripeRedirection from "helpers/hooks/useStripeRedirection";
import useGetPurchaseStatus from "helpers/hooks/useGetPurchaseStatus";
import { PurchaseStatusResponse } from "helpers/interface/alltypes";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/router";

const Page = () => {
  const { handleStripeCheckout } = useStripeRedirection();
  const { data: session } = useSession({ required: true });
  const getPurchaseStatus = useGetPurchaseStatus();
  const router = useRouter();

  const isSubscribeType = router.query.isSubscribeType === "true" ? true : false;

  const onSuccess = (purchaseStatusResponse: PurchaseStatusResponse) => {
    if (session) {
      handleStripeCheckout(
        (router.query.productStripeId as string) || "",
        isSubscribeType
      );
    }
  };

  useEffect(() => {

    if (session && !getPurchaseStatus.data) {
      getPurchaseStatus.mutate(undefined, {
        onSuccess,
      });
    }
  }, [getPurchaseStatus.data, session]);
  return <div></div>;
};

export default Page;
