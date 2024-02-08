import { useEffect, useState } from "react";
import Button from "components/Button";
import useResetPassword from "helpers/hooks/useResetPassword";
import { useRouter } from "next/router";
import useAlert from "helpers/hooks/useAlert";
import AuthError from "components/Error/AuthError";

export default function ResetPassword() {
  const { showAlert } = useAlert();

  const router = useRouter();
  const resetPassword = useResetPassword();
  const [formData, setFormData] = useState({
    password: "",
    confirmPassword: "",
  });
  const [errorShow, setErrorShow] = useState("");

  useEffect(() => {
    if (!router.isReady) return;
    if (!router.query?.token?.length) {
      router.push("/auth/signin");
    }
  }, [router]);

  const onFormChange = (e: any) =>
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));

  const onSubmit = async (e: any) => {
    e.preventDefault();
    setErrorShow("");

    if (formData.password !== formData.confirmPassword) {
      setErrorShow("Password didn't match");
      return;
    }

    const payload = {
      Authorization: (router.query?.token as string) || "",
      new_password: formData.password,
    };

    resetPassword.mutate(payload, {
      onSuccess: async () => {
        showAlert({
          type: "success",
          title: "Password reset successfully",
        });
        router.push("/auth/signin");
      },
      onError: (data: any) => {
        setErrorShow(data.error);
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
          Reset Password
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
                  required
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium leading-6 text-gray-900"
              >
                Confirm Password
              </label>
              <div className="mt-2">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={onFormChange}
                  required
                  className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>

            <div>
              <Button
                isLoading={resetPassword?.isLoading}
                className="flex w-full justify-center"
                type="submit"
              >
                Reset Password
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
