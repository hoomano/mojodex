import React, { useState } from "react";
import Button from "components/Button";
import { OnboardingSteps } from "..";

interface Props {
  onProfileSubmit: (companyWebsite: any) => void;
  onboardingPresentedCheck: any;
}

const Welcome = ({ onProfileSubmit, onboardingPresentedCheck }: Props) => {
  const [companyWebsite, setCompanyWebsite] = useState("");
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
        placeholder="Company Website"
        className="block max-w-[350px] w-full mx-auto rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        required
      />
      <div className="flex justify-center gap-5">
        <Button className="self-center" type="submit">
          Next
        </Button>
        <Button
          variant="secondary"
          onClick={() => onboardingPresentedCheck()}
        >
          Skip
        </Button>
      </div>
    </form>
  );
};

export default Welcome;
