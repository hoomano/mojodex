import Button from "components/Button";
import React, { useState } from "react";
import { OnboardingSteps } from "..";

export interface BusinessDetailsForm {
  correct: any;
  feedback: string;
}

interface Props {
  onBusinessDetailsSubmit: (data: BusinessDetailsForm) => void;
  isLoading: boolean;
  onboardingPresentedCheck: any;
}

const BusinessDetails = ({
  onBusinessDetailsSubmit,
  isLoading,
  onboardingPresentedCheck,
}: Props) => {
  const [formData, setFormData] = useState<BusinessDetailsForm>({
    correct: null,
    feedback: "",
  });

  const onInputChange = (name: string, value: string | boolean) =>
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

  const isFormValid =
    formData.correct || (!formData.correct && !!formData.feedback);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onBusinessDetailsSubmit({
          correct: formData.correct ? "Yes" : "Not really",
          feedback: formData.feedback,
        });
      }}
      className="flex flex-col gap-14"
    >
      <div className="flex gap-5 justify-center">
        <Button
          className="!rounded-[20px] bg-gray-light"
          variant={formData.correct ? "primary" : "outline"}
          onClick={() => onInputChange("correct", true)}
        >
          👍 Yes
        </Button>

        <Button
          variant={formData.correct === false ? "primary" : "outline"}
          className="!rounded-[20px] bg-gray-light"
          onClick={() => onInputChange("correct", false)}
        >
          👎 Not really
        </Button>
      </div>

      <textarea
        rows={3}
        value={formData.feedback}
        onChange={(e) => onInputChange("feedback", e.target.value)}
        name="process_info"
        className="mb-3 block overflow-auto resize-none w-full bg-transparent py-1.5 text-gray-dark placeholder:text-gray-dark focus:ring-0 sm:text-sm sm:leading-6 rounded-md border border-gray-lighter"
        placeholder="Please tell us more anything we need to know about your business."
      />

      <div className="flex justify-center gap-5">
        <Button
          type="submit"
          className="self-center px-5 !m-[unset]"
          variant="primary"
          disabled={!isFormValid}
          isLoading={isLoading}
        >
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

export default BusinessDetails;
