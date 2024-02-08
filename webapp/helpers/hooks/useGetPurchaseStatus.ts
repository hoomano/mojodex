import { useMutation } from "@tanstack/react-query";
import { getPurchaseStatus } from "services/payment";

const useGetPurchaseStatus = () => useMutation(getPurchaseStatus);

export default useGetPurchaseStatus;
