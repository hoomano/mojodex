import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getIsEmailServiceConfigured } from "services/general";

const useIsEmailServiceIsConfigured = () =>
    useQuery([cachedAPIName.IS_EMAIL_SERVICE_CONFIGURED], getIsEmailServiceConfigured);

export default useIsEmailServiceIsConfigured;
