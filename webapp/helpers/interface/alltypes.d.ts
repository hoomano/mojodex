declare module "react-rating-stars-component";

export interface StripeCheckoutSessionResponse {
  sessionId: string;
}

export interface RoleStatusResponse {
  role_status: string;
  free_plan_remaining_days: number;
  current_profile: null;
  available_profiles: AvailableProfile[];
  current_roles: CurrentRoles[];
  last_expired_role: LastExpiredRole[];
}

export interface AvailableProfile {
  profile_pk: number;
  name: string;
  product_stripe_id: string;
  product_apple_id: string;
  n_days_validity: number | null;
  n_tasks_limit: number | null;
  stripe_price: string;
  tasks: string[];
}

export interface CurrentRoles {
  profile_name: string;
  remaining_days: number;
  n_validity_days: number;
  n_tasks_limit: number;
  n_tasks_consumed: number;
  tasks: [];
  is_free_profile: true;
}

export interface LastExpiredRole {
  profile_name: string;
  tasks: [];
  remaining_days: number;
  n_tasks_limit: number;
  n_days_validity: number;
  is_free_profile: true;
  n_tasks_consumed: number;
}
