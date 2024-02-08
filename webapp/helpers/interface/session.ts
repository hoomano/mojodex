export interface UserType {
  name: string;
  email: string;
  image: string;
}

export interface AuthorizationType {
  token: string;
  language_code: string;
  terms_and_conditions_agreed: boolean;
  name: string;
  purchase_status: "no_purchase" | "active";
}

export interface SessionType {
  user: UserType;
  expires: string;
  authorization: AuthorizationType;
}

export interface UpdateSessionResponseType {
  intro_done: boolean;
  session_id: string;
}
