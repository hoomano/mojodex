import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getRoleStatus } from "services/payment";

const useGetRolePlan = () =>
  useQuery([cachedAPIName.ROLE_PLAN], getRoleStatus);

export default useGetRolePlan;
