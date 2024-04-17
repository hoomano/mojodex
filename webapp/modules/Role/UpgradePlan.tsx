import useStripeRedirection from "helpers/hooks/useStripeRedirection";
import { AvailableProfile } from "helpers/interface/alltypes";
import { useTranslation } from "react-i18next";

interface Props {
  availableProfiles: AvailableProfile[];
}

const UpgradePlan = ({ availableProfiles }: Props) => {
  const { handleStripeCheckout } = useStripeRedirection();
  const { t } = useTranslation("dynamic");

  const handleUpgradePlanButton = () => {
    // TODO : Implement handleUpgradePlanButton
    console.log("UpgradePlan > handleUpgradePlanButton > not implemented ");
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {availableProfiles.map((plan) => {
        const isSubscribeType =
          plan.n_days_validity === null && plan.n_tasks_limit === null;

        return (
          <div className="bg-[#E6E6E6] px-6 sm:px-8 py-3 mx-3 sm:mx-5 mt-2 rounded-md">
            <div>
              <div className="font-semibold text-center">{plan?.name}</div>
              <div className="border-[3px] border-[#757575] rounded-md mt-3"></div>
            </div>
            <div className="mt-4 ml-4">
              <div>{t("plan.productCard.includedTasks")}</div>
              {plan?.tasks?.map((task: string, index: number) => (
                <div key={index}>- {task}</div>
              ))}
              <div className="mt-4">{t("plan.productCard.customerSupportByEmail")}</div>
              <div className="mt-4">
                {t("plan.productCard.usageLimitTitle")}
              </div>
              <div>
                -{" "}
                {isSubscribeType
                  ? `${t("plan.productCard.nTasksPerMonth")}`
                  : plan.n_tasks_limit +
                    ` ${t("plan.productCard.nTasksLimitSuffix")}`}
              </div>

              <button
                onClick={() =>
                  handleStripeCheckout(plan.product_stripe_id, isSubscribeType)
                }
                className="w-full bg-[#1995FA] text-white border-[7px] rounded-[20px] py-1 px-3 border-[#147BCB] mt-3"
              >
                {isSubscribeType
                  ? `Subscribe for ${plan.stripe_price} / month`
                  : `Buy Now for ${plan.stripe_price}`}
              </button>
              <div className="my-2 text-[#949494]">
              {t("plan.productCard.customPlanCallToAction")}
              </div>
              <button
                className="w-full bg-[#1995FA] text-white border-[6px] rounded-2xl py-1 px-3 border-[#147BCB] mb-2"
                onClick={handleUpgradePlanButton}
              >
                {t("plan.productCard.contactUsButton")}
              </button>
              <div className="text-[#949494] text-base pb-3">
              {t("plan.productCard.getQuoteCallToAction")}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default UpgradePlan;
