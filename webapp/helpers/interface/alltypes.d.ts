declare module "react-rating-stars-component";

export interface StripeCheckoutSessionResponse {
  sessionId: string;
}

export interface PurchaseStatusResponse {
  purchase_status: string;
  free_plan_remaining_days: number;
  current_product: null;
  purchasable_products: PurchasableProducts[];
  current_purchases: CurrentPurchases[];
  last_expired_purchase: LastExpiredPurchase[];
}

export interface PurchasableProducts {
  product_pk: number;
  name: string;
  product_stripe_id: string;
  product_apple_id: string;
  n_days_validity: number | null;
  n_tasks_limit: number | null;
  stripe_price: string;
  tasks: string[];
}

export interface CurrentPurchases {
  product_name: string;
  remaining_days: number;
  n_validity_days: number;
  n_tasks_limit: number;
  n_tasks_consumed: number;
  tasks: [];
  is_free_product: true;
}

export interface LastExpiredPurchase {
  product_name: string;
  tasks: [];
  remaining_days: number;
  n_tasks_limit: number;
  n_days_validity: number;
  is_free_product: true;
  n_tasks_consumed: number;
}
