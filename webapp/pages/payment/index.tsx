import React, { useEffect } from "react";
import Layout from "components/Layout";
import useGetRoleStatus from "helpers/hooks/useGetRoleStatus";
import { useSession } from "next-auth/react";
import { RoleStatusResponse } from "helpers/interface/alltypes";
import Loader from "components/Loader";
import { useTranslation } from "react-i18next";

const Payment = () => {
  const { update, data: session }: any = useSession();
  const getRoleStatus = useGetRoleStatus();
  const { t } = useTranslation("dynamic");

  const onSuccess = (roleStatusResponse: RoleStatusResponse) => {
    if (session && roleStatusResponse?.role_status === "active") {
      const updatedSession = {
        ...session,
        authorization: {
          ...session.authorization,
          ...roleStatusResponse,
        },
      };
      update(updatedSession);
    }
  };

  useEffect(() => {
    if (session && !getRoleStatus.data) {
      getRoleStatus.mutate(undefined, {
        onSuccess,
      });
    }
  }, [getRoleStatus.data, session]);

  if (!getRoleStatus.data) {
    return (
      <Layout>
        <div className="h-screen w-full flex justify-center items-center">
          <div>
            <Loader />
          </div>
        </div>
      </Layout>
    );
  }

  if (getRoleStatus.data?.role_status === "active") {
    return (
      <Layout>
        <div className="flex h-screen">
          <div className="max-w-[580px] text-center m-auto">
            <div className="text-h2 font-semibold">
              {t("plan.purchaseMessages.success.emoji")}
            </div>
            <div className="text-h2 font-semibold">
              {t("plan.purchaseMessages.success.title")}
            </div>
            <div className="text-xl text-gray-lighter">
              {t("plan.purchaseMessages.success.body")}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="flex h-screen">
        <div className="max-w-[580px] text-center m-auto">
          <div className="text-h2 font-semibold">
            {t("plan.purchaseMessages.canceled.emoji")}{" "}
            {t("plan.purchaseMessages.canceled.title")}
          </div>
          <div className="text-xl text-gray-lighter">
            {t("plan.purchaseMessages.canceled.body")}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Payment;
