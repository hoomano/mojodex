import type {
  GetServerSidePropsContext,
  InferGetServerSidePropsType,
} from "next";
import { getProviders, signIn } from "next-auth/react";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../api/auth/[...nextauth]";
import { useState } from "react";
import Button from "components/Button";
import AuthError from "components/Error/AuthError";
import { useRouter } from "next/router";
import AuthMobileView from "components/AuthMobileView";

export default function SignIn({
  providers,
  callbackUrl,
}: InferGetServerSidePropsType<typeof getServerSideProps>) {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
  });
  const [errorShow, setErrorShow] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const customSignIn = async (providerId: string) => {
    signIn(providerId, {
      callbackUrl: router.query.extension === "true" ? "/extension" : "/tasks",
    });
  };

  const onFormChange = (e: any) =>
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));

  let LoginButton = (provider: any) => {
    if (provider.name == "Google") {
      return GoogleLoginButton(provider);
    } else if (provider.name == "Azure Active Directory") {
      return MicrosoftLoginButton(provider);
    } else if (provider.name == "Apple") {
      return AppleLoginButton(provider);
    }
  };

  let GoogleLoginButton = (provider: any) => {
    return (
      <div
        key={provider.name}
        className="bg-white mt-2 p-2 rounded-md  border hover:bg-gray-100"
      >
        <button
          onClick={() => customSignIn(provider.id)}
          className="text-black flex justify-between w-full p-1 items-center"
        >
          <img id="provider-logo" src="/images/google.svg"></img>
          <div className="text-mg">Google</div>
          <div></div>
        </button>
      </div>
    );
  };

  let MicrosoftLoginButton = (provider: any) => {
    return (
      <div
        key={provider.name}
        className="bg-white mt-2 p-2 rounded-md  border hover:bg-gray-100"
      >
        <button
          onClick={() => customSignIn(provider.id)}
          className="text-black flex justify-between w-full p-1 items-center"
        >
          <img id="provider-logo" src="/images/microsoft.svg"></img>
          <div className="text-mg">Microsoft</div>
          <div></div>
        </button>
      </div>
    );
  };

  let AppleLoginButton = (provider: any) => {
    return (
      <div
        key={provider.name}
        className="bg-white mt-2 p-2 rounded-md border hover:bg-gray-100"
      >
        <button
          onClick={() => customSignIn(provider.id)}
          className="text-black flex justify-between w-full p-1 items-center"
        >
          <img id="provider-logo" src="/images/apple.svg"></img>
          <div className="text-mg">Apple</div>
          <div></div>
        </button>
      </div>
    );
  };

  const onSubmit = async (e: any) => {
    e.preventDefault();
    setErrorShow("");

    try {
      setIsLoading(true);
      const signUpResponse = await signIn("email_password_signup", {
        ...formData,
        redirect: false,
      });

      if (signUpResponse?.error) {
        setIsLoading(false);
        setErrorShow(signUpResponse.error);
      }

      if (!signUpResponse?.error && signUpResponse?.url) {
        if (callbackUrl != undefined) {
          router.push(callbackUrl as string);
          return;
        }
        router.push("/tasks");
      }
    } catch (error) {
      setIsLoading(false);
      setErrorShow(
        "Oops, something weird happened. Please contact us by email!"
      );
    }
  };

  var isFromMobile = false;
  if (callbackUrl != undefined) {
    var data: String[];
    data = (callbackUrl as String).split("?");
    var indexRedirectUri = data.indexOf("redirect_uri=mobile");
    if (indexRedirectUri !== -1) {
      isFromMobile = true;
    }
  }

  return (
    <>
      <div
        className={`bg-white min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8 ${
          isFromMobile ? "" : "hidden sm:flex"
        }`}
      >
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img
            className="mx-auto h-10 w-auto"
            src="/images/logo/mojodex_logo.png"
            alt="Mojodex"
          />
          <h2 className="mt-6 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
            Create an account
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <form className="space-y-6" onSubmit={onSubmit}>
              {errorShow && (
                <AuthError
                  title={errorShow}
                  onclickHandler={() => setErrorShow("")}
                />
              )}
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Name
                </label>
                <div className="mt-2">
                  <input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={onFormChange}
                    required
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Email address
                </label>
                <div className="mt-2">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={onFormChange}
                    autoComplete="email"
                    required
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium leading-6 text-gray-900"
                >
                  Password
                </label>
                <div className="mt-2">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={onFormChange}
                    autoComplete="current-password"
                    required
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                  />
                </div>
              </div>

              <div>
                <Button
                  isLoading={isLoading}
                  type="submit"
                  className="flex w-full justify-center"
                >
                  Sign up
                </Button>
              </div>
            </form>

            <div>
              <div className="relative mt-10">
                <div
                  className="absolute inset-0 flex items-center"
                  aria-hidden="true"
                >
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-sm font-medium leading-6">
                  <span className="bg-white px-6 text-gray-900">
                    Or continue with
                  </span>
                </div>
              </div>
              <div>
                {Object.values(providers ?? []).map((provider) =>
                  LoginButton(provider)
                )}
              </div>
            </div>
          </div>
          <div className="text-white text-sm mt-2"></div>
        </div>
      </div>
      {!isFromMobile && <AuthMobileView />}
    </>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  const session = await getServerSession(
    context.req,
    context.res,
    authOptions as any
  );

  // If the user is already logged in, redirect.
  // Note: Make sure not to redirect to the same page
  // To avoid an infinite loop!
  if (session) {
    return { redirect: { destination: "/" } };
  }

  const { callbackUrl } = context.query;
  const providers = await getProviders();

  let localProps;
  if (callbackUrl != undefined)
    localProps = { callbackUrl: callbackUrl, providers: providers };
  else localProps = { providers: providers };
  return { props: localProps };
}
