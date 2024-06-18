import { useState } from "react";
import Button from "components/Button";
import useForgotPassword from "helpers/hooks/useForgotPassword";
import useAlert from "helpers/hooks/useAlert";
import AuthError from "components/Error/AuthError";
import { useTranslation } from "react-i18next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const initialFormValue = { email: "" };

export default function ForgotPassword() {
  const forgotPassword = useForgotPassword();
  const [formData, setFormData] = useState(initialFormValue);
  const [errorShow, setErrorShow] = useState("");
  const { showAlert } = useAlert();
  const { t } = useTranslation("dynamic");

  const resetFormHandler = () => {
    setFormData(initialFormValue);
  };

  const onFormChange = (e: any) =>
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));

  const onSubmit = async (e: any) => {
    e.preventDefault();
    setErrorShow("");

    forgotPassword.mutate(formData.email, {
      onSuccess: () => {
        showAlert({
          title: t("account.forgotPassword.emailAddress"),
          type: "success",
        });
        resetFormHandler();
      },
      onError: ({ error }: any) => {
        setErrorShow(error);
      },
    });
  };

  return (
    <div className="flex bg-white min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <img
          className="mx-auto h-10 w-auto"
          src="/images/logo/mojodex_logo.png"
          alt="Mojodex"
        />
        <h2 className="mt-6 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
          {t("account.forgotPassword.title")}
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
                {t("account.forgotPassword.emailAddress")}
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
              <Button
                isLoading={forgotPassword?.isLoading}
                className="flex w-full justify-center"
                type="submit"
              >
                {t("account.forgotPassword.button")}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}