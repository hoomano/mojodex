import useStripeRedirection from "helpers/hooks/useStripeRedirection";
import useGetRoleStatus from "helpers/hooks/useGetRoleStatus";
import { RoleStatusResponse } from "helpers/interface/alltypes";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/router";

const Page = () => {
  const { handleStripeCheckout } = useStripeRedirection();
  const { data: session } = useSession({ required: true });
  const getRoleStatus = useGetRoleStatus();
  const router = useRouter();

  const isSubscribeType = router.query.isSubscribeType === "true" ? true : false;

  const onSuccess = (roleStatusResponse: RoleStatusResponse) => {
    if (session) {
      handleStripeCheckout(
        (router.query.productStripeId as string) || "",
        isSubscribeType
      );
    }
  };

  useEffect(() => {

    if (session && !getRoleStatus.data) {
      getRoleStatus.mutate(undefined, {
        onSuccess,
      });
    }
  }, [getRoleStatus.data, session]);
  return <div></div>;
};

export default Page;
