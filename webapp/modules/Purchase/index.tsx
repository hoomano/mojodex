import useGetPurchasePlan from "helpers/hooks/useGetPurchasePlan";
import CurrentPlan from "./CurrentPlan";
import UpgradePlan from "./UpgradePlan";
import Loader from "components/Loader";
import { useTranslation } from "react-i18next";

const Purchase = () => {
  const { data, isLoading } = useGetPurchasePlan();
  const { t } = useTranslation("dynamic");

  if (!data || isLoading) {
    return <Loader />;
  }

  const { current_purchases, last_expired_purchase } = data;

  return (
    <div className="bg-white py-8 px-4 sm:py-12 sm:px-6">
      <div className="text-lg font-medium">{t("plan.title")}</div>
      <div className="mt-6 sm:mt-10">{t("plan.currentPlans")}</div>
      <CurrentPlan
        currentData={
          current_purchases?.length ? current_purchases : last_expired_purchase
        }
        isCurrentPurchaseActive={!!current_purchases.length}
      />
      {!!data?.purchasable_products?.length && (
        <div className="mt-12 mb-4">{t("plan.updatePlan")}</div>
      )}
      <UpgradePlan purchasableProducts={data?.purchasable_products || []} />
    </div>
  );
};

export default Purchase;
