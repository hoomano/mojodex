import { useTranslation } from "react-i18next";

interface Props {
  currentData: any;
  isCurrentPurchaseActive: boolean;
}

const CurrentPlan = ({ currentData, isCurrentPurchaseActive }: Props) => {
  const { t } = useTranslation("dynamic");

  return (
    <>
      {currentData?.map((plan: any) => {
        const isValidityCheck =
          (plan.n_validity_days === null || plan.n_days_validity === null) &&
          plan.n_tasks_limit === null;

        const isRemainingDays =
          plan.remaining_days === null &&
          (plan.n_validity_days === null || plan.n_days_validity === null);

        return (
          <div className="bg-[#E6E6E6] px-6 sm:px-9 py-3 mx-3 sm:mx-5 mt-3 rounded-md">
            <div className="w-fit flex items-center gap-8 sm:gap-10">
              <div>
                <div className="font-semibold">{plan?.product_name}</div>
                <div className="border-[3px] border-[#757575] rounded-md mt-3"></div>
              </div>
              <button
                className={`text-sm rounded-2xl py-1 px-3 ${
                  isCurrentPurchaseActive
                    ? "bg-[#C0D9C6] text-[#54AA4A]"
                    : "bg-[#ebc1c6] text-[#f0274d]"
                } self-start`}
              >
                {isCurrentPurchaseActive
                  ? `${t("plan.purchaseBadge.activeState")}`
                  : `${t("plan.purchaseBadge.expiredState")}`}
              </button>
            </div>
            <div className="block sm:flex justify-between items-center">
              <div className="mt-4 ml-4 w-1/2">
                <div>{t("plan.productCard.includedTasks")}</div>
                {plan?.tasks?.map((task: string, index: number) => (
                  <div key={index}>- {task}</div>
                ))}
                <div className="mt-4">
                  {t("plan.productCard.customerSupportByEmail")}
                </div>
                <div className="mt-4">
                  {t("plan.productCard.usageLimitTitle")}
                </div>
                {isValidityCheck ? (
                  -`${t("plan.productCard.nTasksPerMonth")}`
                ) : (
                  <>
                    {!isRemainingDays && (
                      <div>
                        -{" "}
                        {isCurrentPurchaseActive
                          ? plan.n_validity_days || 0
                          : plan.n_days_validity || 0}{" "}
                        {t("plan.productCard.nValidityDaysSuffix")}
                      </div>
                    )}
                    {!isValidityCheck && (
                      <div>
                        - {plan.n_tasks_limit ? plan.n_tasks_limit : 0}{" "}
                        {t("plan.productCard.nTasksLimitSuffix")}
                      </div>
                    )}
                  </>
                )}
              </div>
              {!isValidityCheck && (
                <div className="bg-white px-3 py-1 rounded-md w-fit pr-6 my-4 sm:my-0">
                  <div className="text-xl font-semibold">
                    {t("plan.purchaseUsageCard.title")}
                  </div>
                  {!isValidityCheck && (
                    <div className="mt-1 pl-4">
                      {t("plan.purchaseUsageCard.nTaskDone")}{" "}
                      .........................{" "}
                      {plan.n_tasks_consumed ? plan.n_tasks_consumed : 0} /{" "}
                      {plan.n_tasks_limit ? plan.n_tasks_limit : 0}
                    </div>
                  )}
                  {!isRemainingDays && (
                    <div className="pl-4">
                      {t("plan.purchaseUsageCard.nDaysLeft")}{" "}
                      .............................{" "}
                      {plan.remaining_days ? plan.remaining_days : 0} /{" "}
                      {isCurrentPurchaseActive
                        ? plan.n_validity_days || 0
                        : plan.n_days_validity || 0}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </>
  );
};

export default CurrentPlan;
