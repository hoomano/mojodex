import React, { useEffect } from "react";
import Layout from "components/Layout";
import useGetPurchaseStatus from "helpers/hooks/useGetPurchaseStatus";
import { useSession } from "next-auth/react";
import { PurchaseStatusResponse } from "helpers/interface/alltypes";
import Loader from "components/Loader";
import { useTranslation } from "react-i18next";

const Payment = () => {
  const { update, data: session }: any = useSession();
  const getPurchaseStatus = useGetPurchaseStatus();
  const { t } = useTranslation("dynamic");

  const onSuccess = (purchaseStatusResponse: PurchaseStatusResponse) => {
    if (session && purchaseStatusResponse?.purchase_status === "active") {
      const updatedSession = {
        ...session,
        authorization: {
          ...session.authorization,
          ...purchaseStatusResponse,
        },
      };
      update(updatedSession);
    }
  };

  useEffect(() => {
    if (session && !getPurchaseStatus.data) {
      getPurchaseStatus.mutate(undefined, {
        onSuccess,
      });
    }
  }, [getPurchaseStatus.data, session]);

  if (!getPurchaseStatus.data) {
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

  if (getPurchaseStatus.data?.purchase_status === "active") {
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
