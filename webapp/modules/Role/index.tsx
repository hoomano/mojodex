import useGetRolePlan from "helpers/hooks/useGetRolePlan";
import CurrentPlan from "./CurrentPlan";
import UpgradePlan from "./UpgradePlan";
import Loader from "components/Loader";
import { useTranslation } from "react-i18next";

const Role = () => {
  const { data, isLoading } = useGetRolePlan();
  const { t } = useTranslation("dynamic");

  if (!data || isLoading) {
    return <Loader />;
  }

  const { current_roles, last_expired_role } = data;

  return (
    <div className="bg-white py-8 px-4 sm:py-12 sm:px-6">
      <div className="text-lg font-medium">{t("plan.title")}</div>
      <div className="mt-6 sm:mt-10">{t("plan.currentPlans")}</div>
      <CurrentPlan
        currentData={
          current_roles?.length ? current_roles : last_expired_role
        }
        isCurrentRoleActive={!!current_roles.length}
      />
      {!!data?.available_profiles?.length && (
        <div className="mt-12 mb-4">{t("plan.updatePlan")}</div>
      )}
      <UpgradePlan availableProfiles={data?.available_profiles || []} />
    </div>
  );
};

export default Role;
