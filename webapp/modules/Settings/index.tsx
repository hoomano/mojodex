import { useState } from "react";
import useAlert from "helpers/hooks/useAlert";
import useGetLanguageCode, {
  useGetLanguageCodeMutation,
} from "helpers/hooks/useGetLanguageCode";
import useLanguageCode from "helpers/hooks/useLanguageCode";
import { useSession } from "next-auth/react";
import Image from "next/image";
import { useRouter } from "next/router";
import { AiOutlineRight } from "react-icons/ai";
import { useTranslation } from "react-i18next";
import axiosClient from "services/config/axiosClient";

const Settings = () => {
  const { update: updateAuthSession, data: session }: any = useSession();
  const router = useRouter();
  const { showAlert } = useAlert();
  const languageCode = useLanguageCode();
  const { t } = useTranslation("dynamic");

  const [selectedLanguage, setSelectedLanguage] = useState(
    session?.authorization?.language_code
  );

  const { data: languageInfo, isLoading } = useGetLanguageCode(
    session?.authorization?.language_code || router.locale
  );

  // retrieve the link to the data policy from an environment variable if it exists
  const dataPolicyLink = process.env.NEXT_PUBLIC_DATA_POLICY_LINK;

  // retrieve the link to the terms of use from an environment variable if it exists
  const termsOfUseLink = process.env.NEXT_PUBLIC_TERMS_OF_USE_LINK

  const { mutate: getLanguageJson } = useGetLanguageCodeMutation();

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLanguageCode = e.target.value;
    languageCode.mutate(
      { language_code: newLanguageCode },
      {
        onSuccess: async () => {
          showAlert({
            title: "Language updated successfully.",
            type: "success",
          });
          updateAuthSession({
            ...session,
            authorization: {
              ...session.authorization,
              language_code: newLanguageCode,
            },
          });
          localStorage.removeItem("language_code");

          getLanguageJson(newLanguageCode, {
            onSuccess: async (data) => {
              await axiosClient.post("/api/create-lang-file", {
                fileJson: data?.language_json_file,
                lang: newLanguageCode,
              });
              router.push(router.pathname, router.pathname, {
                locale: newLanguageCode,
              });
            },
          });
        },
      }
    );
    setSelectedLanguage(newLanguageCode);
  };

  return (
    <div className="flex justify-center h-screen">
      <div className="bg-white py-12 px-6 sm:py-12 lg:px-8">
        <Image
          className="h-18 w-18 rounded-xl cursor-pointer flex m-auto"
          src={
            session?.user?.image
              ? session.user.image
              : "/images/default_user.png"
          }
          alt=""
          width={60}
          height={60}
        />
        <div className="text-center mt-2 mb-6">
          {session?.authorization?.name}
        </div>

        <div className="text-xl font-bold mb-2">
          {t("account.accountSectionTitle")}
        </div>
        <div
          className="bg-[#F3F4F6] px-3 py-2 w-[250px] rounded-md flex justify-between items-center cursor-pointer"
          onClick={() => router.push("/role")}
        >
          <span>{t("account.planButton")}</span>
          <span className="text-gray-400 text-sm">
            <AiOutlineRight />
          </span>
        </div>

        <div
          className="bg-[#F3F4F6] px-3 py-2 w-[250px] rounded-md flex justify-between items-center mt-2 cursor-pointer"
          onClick={() => router.push("/delete-account")}
        >
          <span>{t("account.deleteAccountButton")}</span>
          <span className="text-gray-400 text-sm">
            <AiOutlineRight />
          </span>
        </div>

        <div className="text-xl font-bold my-3">
          {t("account.securitySectionTitle")}
        </div>


        {
          termsOfUseLink &&
          <div
            className="bg-[#F3F4F6] px-3 py-2 w-[250px] rounded-md flex justify-between items-center cursor-pointer"
            onClick={() => router.push(termsOfUseLink)}
          >
            <span>{t("account.termsOfUseButton")}</span>
            <span className="text-gray-400 text-sm">
              <AiOutlineRight />
            </span>
          </div>
        }

        {
          // if the data policy link is available, display the data policy button
          dataPolicyLink &&
          <div
            className="bg-[#F3F4F6] px-3 py-2 w-[250px] rounded-md flex justify-between items-center mt-2 cursor-pointer"
            onClick={() => router.push(dataPolicyLink)}
          >
            <span>{t("account.privacyPolicyButton")}</span>
            <span className="text-gray-400 text-sm">
              <AiOutlineRight />
            </span>
          </div>
        }

        <div className="bg-[#F3F4F6] px-3 py-2 w-[250px] rounded-md flex justify-between items-center mt-2 cursor-pointer">
          <span>{t("account.languageButton")}</span>
          {isLoading ? (
            <div className="button-loader"></div>
          ) : (
            <select
              value={router.locale}
              onChange={handleLanguageChange}
              className="text-gray-400 text-sm py-1 rounded-md pr-7 bg-transparent focus:ring-0"
            >
              {languageInfo?.available_languages &&
                Object.entries(languageInfo.available_languages).map(
                  ([key, value]) => (
                    <option key={key} value={key}>
                      {value as any}
                    </option>
                  )
                )}
            </select>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
