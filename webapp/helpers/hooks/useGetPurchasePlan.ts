import { useQuery } from "@tanstack/react-query";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { getPurchaseStatus } from "services/payment";

const useGetPurchasePlan = () =>
  useQuery([cachedAPIName.PURCHASE_PLAN], getPurchaseStatus);

export default useGetPurchasePlan;
