# How Products work?

## Free trial
At onboarding, new users are asked to select a product category. This category will define the user's profile and will automatically affect them the free trial product of this category.
This allows users to try the product for a limited time or a limited number of tasks through a tailored experience matching their profile.

## Moving on with other products
Any time, the user can be affected products:
- manually by an admin using Backoffice APIs
- automatically by the payment system when buying a product (see below)

This allow users to keep a tailored experience matching their profile and needs.

### Buying a product using an implemented payment service

2 payment services have been implemented for now:

### Stripe
When the user wants to buy a product though Stripe, here is the flow:

1. A Stripe session is created (`webapp/helpers/hooks/useCreateStripeCheckoutSession.ts`)
2. The Backend route PUT `/purchase` (`backend/app/routes/purchase.py`) is called specifying the stripe_session_id. This route creates a new purchase that is not active yet.
3. The user is redirected to the Stripe checkout page
4. The user pays for the product and is redirected to Mojodex's success page
5. Stripe uses the `new purchase` webhook to notify Mojodex that the purchase is successful: POST `/purchase` (`backend/app/routes/purchase.py`). This route activates the purchase by:
- deactivating any previous active subscription if bought product is a subscription 
- associating and enabling the product's tasks to the user

If the product bought is a subscription, it will be kept active and no Stripe webhook will be call as long as user's payments are up to date. If a payment fails, Stripe calls a webhook to handle the end of a purchase: POST `/subscription_end` (`backend/app/routes/purchase_end_stripe_webhook.py`).

### Apple in-app purchase
When the user wants to buy a product though Apple in-app purchase, here is the flow:

1. The user is redirected to the Apple in-app purchase flow
2. The user pays for the product and is redirected to Mojodex's success page. Apple calls webhook POST `/in_app_apple_purchase` (`backend/app/routes/inapp_apple_purchase.py`). This routes verifies the transaction and created an inactive purchase, not yet associated to a user.
3. The application calls route PUT `/in_app_apple_purchase` to confirm the purchase and associate it to the user (`backend/app/routes/inapp_apple_purchase.py`). This route activates the purchase by:
- deactivating any previous active subscription if bought product is a subscription 
- associating and enabling the product's tasks to the user

On the contrary of Stripe, regarding subscriptions, Apple does call the `/in_app_apple_purchase` webhook every month at payment renewal providing a new transaction ID. Old subscription purchase is deactived, a new purchase is created and associated to the user.
This `/in_app_apple_purchase` is also used to manage failed renewals, grace period and purchases expirations.
