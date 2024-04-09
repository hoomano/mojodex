import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import AzureADProvider from "next-auth/providers/azure-ad";
import CredentialsProvider from "next-auth/providers/credentials";
import AppleProvider from "next-auth/providers/apple";
import axios from "axios";
import { appVersion, appPlatform } from "helpers/constants/index";

const createAuthPayload = (user, account, credentials) => {
  let payload = {
    email: user.email,
    datetime: new Date().toISOString(),
    login_method: "email_password",
    password: "",
    version: appVersion,
    platform: appPlatform
  };

  if (account.provider === "google") {
    payload["login_method"] = "google";
    payload["google_token"] = account.id_token;
  }

  if (account.provider === "azure-ad") {
    payload["login_method"] = "microsoft";
    payload["microsoft_token"] = account.access_token;
  }

  if (account.provider === "apple") {
    payload["login_method"] = "apple";
    payload["apple_token"] = account.id_token;
  }

  if (account.provider === "email_password_login") {
    payload["email"] = credentials.email;
    payload["password"] = credentials.password;
  }

  if (account.provider === "email_password_signup") {
    payload["email"] = credentials.email;
    payload["password"] = credentials.password;
    payload["name"] = credentials.name;
  }

  return payload;
};

export const authOptions = {
  // Configure one or more authentication providers
  providers: [
    // Check if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are defined before adding GoogleProvider
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET ? [
      GoogleProvider({
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      }),
    ] : []),
    // Check if AZURE_AD_CLIENT_ID and AZURE_AD_CLIENT_SECRET are defined before adding AzureADProvider
    ...(process.env.AZURE_AD_CLIENT_ID && process.env.AZURE_AD_CLIENT_SECRET ? [
      AzureADProvider({
        clientId: process.env.AZURE_AD_CLIENT_ID,
        clientSecret: process.env.AZURE_AD_CLIENT_SECRET,
        authorization: { params: { scope: "openid profile user.Read email" } },
      }),
    ] : []),
    // Check if APPLE_ID and APPLE_SECRET are defined before adding AppleProvider
    ...(process.env.APPLE_ID && process.env.APPLE_SECRET ? [
      AppleProvider({
        clientId: process.env.APPLE_ID,
        clientSecret: process.env.APPLE_SECRET,
      }),
    ] : []),
    CredentialsProvider({
      id: "email_password_login",
      name: "Login",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        return credentials;
      },
    }),
    CredentialsProvider({
      id: "email_password_signup",
      name: "Signup",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
        name: { label: "Name", type: "text" },
      },
      async authorize(credentials) {
        return credentials;
      },
    }),
  ],
  cookies: {
    pkceCodeVerifier: {
      name: "next-auth.pkce.code_verifier",
      options: {
        httpOnly: true,
        sameSite: "none",
        path: "/",
        secure: true,
      },
    },
  },
  secret: process.env.NEXT_AUTH_JWT_SECRET,
  theme: {
    logo: "/images/logo/mojodex_logo.png",
  },
  pages: {
    signIn: "/auth/signin",
  },
  session: {
    jwt: true,
    maxAge: 86400 * 30, // 1 hours * 30
  },
  callbacks: {
    async redirect({ url, baseUrl }) {
      if (
        url.startsWith(baseUrl + "/auth/signin") ||
        url.startsWith(baseUrl + "/auth/signup")
      ) {
        let callBackUri = url.split("?callbackUrl=");
        if (callBackUri.length > 1) {
          callBackUri = callBackUri[1].split("&error=SessionRequired")[0];
          callBackUri = callBackUri.replace(/%2F/g, "/");
          callBackUri = callBackUri.replace(/%3A/g, ":");
          callBackUri = callBackUri.replace(/%3F/g, "?");
          callBackUri = callBackUri.replace(/%3D/g, "=");
          callBackUri = callBackUri.replace(/%26/g, "&");
          return callBackUri;
        }
      }
      // Allows relative callback URLs
      if (url.startsWith("/")) return `${baseUrl}${url}`;
      // Allows callback URLs on the same origin
      else if (new URL(url).origin === baseUrl) return url;
      return baseUrl;
    },
    async signIn({ user, account, credentials }) {
      try {
        const payload = createAuthPayload(user, account, credentials);
        const { data } = await axios({
          url: process.env.MOJODEX_BACKEND_URI + "/user",
          method: account.provider === "email_password_signup" ? "put" : "post",
          data: payload,
        });
        

        user.authorization = data;

        try {
          const { data: onboardingInfo } = await axios.get(
            process.env.MOJODEX_BACKEND_URI + "/onboarding",
            {
              params: { datetime: new Date().toISOString() },
              headers: { Authorization: data.token },
            }
          );
          user.authorization.onboarding_presented =
            onboardingInfo?.onboarding_presented || false;
        } catch (error) {
          console.log(error);
        }

        if (data?.token) {
          return true;
        } else {
          return false;
        }
      } catch (error) {
        throw new Error(
          error?.response?.data?.error ||
            "Oops, something weird happened. Please contact us by email!"
        );
      }
    },
    jwt(jwtProps) {
      const { token, user, session, trigger } = jwtProps;
      if (user) {
        token.accessToken = user.accessToken;
        token.authorization = user.authorization;
      }
      if (trigger === "update") {
        token.authorization = session.authorization;
      }
      return token;
    },
    session({ session, token }) {
      if (token?.authorization) {
        session.authorization = token.authorization;
      }
      return session;
    },
  },
};

export default NextAuth(authOptions);
