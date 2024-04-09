import React, { useState } from "react";
import Button from "components/Button";
import { OnboardingSteps } from "..";
import { useTranslation } from "react-i18next";

interface Props {
  onProfileSubmit: (companyWebsite: any) => void;
  onboardingPresentedCheck: any;
}

const Welcome = ({ onProfileSubmit, onboardingPresentedCheck }: Props) => {
  const [companyWebsite, setCompanyWebsite] = useState("");
  const { t } = useTranslation("dynamic");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onProfileSubmit(companyWebsite);
      }}
      className="flex flex-col gap-14"
    >
      <input
        type="url"
        name="companyWebsite"
        value={companyWebsite}
        onChange={(e) => setCompanyWebsite(e.target.value)}
        placeholder={t("onboarding.webUrlInputPage.webUrlInputHintText")}
        className="block max-w-[350px] w-full mx-auto rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        required
      />
      <div className="flex justify-center gap-5">
        <Button className="self-center" type="submit">
          {t("nextButton")}
        </Button>
        <Button
          variant="secondary"
          onClick={() => onboardingPresentedCheck()}
        >
          {t("skipContainerButton")}
        </Button>
      </div>
    </form>
  );
};

export default Welcome;
