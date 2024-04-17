import Stripe from "stripe";
import axios from "axios";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  if (req.method === "GET") {
    const { isSubscribeType, productStripeId } = req.query;
    const paymentMode = isSubscribeType === "true" ? "subscription" : "payment";

    if (!productStripeId) {
      throw new Error("Product Stripe ID not found");
    }

    try {
      const prices = await stripe.prices.list({
        product: req.query.productStripeId,
      });

      const redirectUrl = `${process.env.MOJODEX_WEBAPP_URI}/payment`;

      const checkoutSession = await stripe.checkout.sessions.create({
        line_items: [
          {
            price: prices.data[0].id,
            quantity: 1,
          },
        ],
        mode: paymentMode,
        allow_promotion_codes: true,
        success_url: `${redirectUrl}?success=true`,
        cancel_url: `${redirectUrl}?canceled=true`,
      });

      const rolePayload = {
        datetime: new Date().toISOString(),
        stripe_session_id: checkoutSession.id,
        product_stripe_id: productStripeId,
      };

      const response = await axios.put(
        `${process.env.MOJODEX_BACKEND_URI}/role`,
        rolePayload,
        { headers: { Authorization: req.headers.token } }
      );

      if (response.data?.role_pk) {
        return res.status(200).json({ sessionId: checkoutSession.id });
      } else {
        throw new Error("Unable to create transactions");
      }
    } catch (err) {
      console.log(err?.response?.data);
      return res
        .status(500)
        .json({ error: err?.message || "Error creating checkout session" });
    }
  } else {
    res.setHeader("Allow", "GET");
    res.status(405).end("Method Not Allowed");
  }
}
