import { useMutation } from "@tanstack/react-query";
import { createStripeCheckoutSession } from "services/payment";

const useCreateStripeCheckoutSession = () =>
  useMutation(createStripeCheckoutSession);

export default useCreateStripeCheckoutSession;
