import { loadStripe } from "@stripe/stripe-js";
import useCreateStripeCheckoutSession from "./useCreateStripeCheckoutSession";

const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || ""
);

const useStripeRedirection = () => {
  const createStripeCheckoutSession = useCreateStripeCheckoutSession();

  const handleStripeCheckout = async (
    productStripeId: string,
    isSubscribeType: boolean
  ) => {
    try {
      const stripe = await stripePromise;
      if (!stripe) return;

      createStripeCheckoutSession.mutate(
        { productStripeId, isSubscribeType },
        {
          onSuccess: async (response) => {
            if (response?.sessionId) {
              const data = await stripe.redirectToCheckout({
                sessionId: response.sessionId,
              });
              if (data.error) throw data.error;
            }
          },
        }
      );
    } catch (err) {
      console.error("Error in creating checkout session:", err);
    }
  };

  return { handleStripeCheckout };
};

export default useStripeRedirection;
