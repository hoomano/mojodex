import Button from "components/Button";
import React, { useState } from "react";

interface Props {
  onSubmit: (data: string) => void;
  isLoading: boolean;
  onboardingPresentedCheck: () => void;
}

const suggestedGoalList = [
  "Enhance lead conversion",
  "Strengthen current customer connections",
  "Discover Mojodex",
];

const Goals = ({ onSubmit, isLoading, onboardingPresentedCheck }: Props) => {
  const [goal, setGoal] = useState("");
  const [goalInput, setGoalInput] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(goal || goalInput);
      }}
      className="flex flex-col gap-3 w-full max-w-[350px] mx-auto"
    >
      {suggestedGoalList.map((suggestedGoal) => (
        <Button
          key={suggestedGoal}
          type="button"
          className="bg-gray-light"
          variant={suggestedGoal === goal ? "primary" : "outline"}
          onClick={() => {
            setGoal(suggestedGoal);
            setGoalInput("");
          }}
        >
          {suggestedGoal}
        </Button>
      ))}

      <textarea
        rows={2}
        value={goalInput}
        onChange={(e) => {
          setGoalInput(e.target.value);
          setGoal("");
        }}
        name="goal_info"
        className="mt-4 mb-3 block overflow-auto resize-none w-full bg-transparent py-1.5 text-gray-dark placeholder:text-gray-dark focus:ring-0 sm:text-sm sm:leading-6 rounded-md border border-gray-lighter"
        placeholder="Or state your goal in your own words"
      />

      <div className="flex justify-center gap-5">
        <Button
          type="submit"
          className="self-center px-5 disabled:opacity-50"
          variant="primary"
          disabled={!goal && !goalInput}
          isLoading={isLoading}
        >
          Next
        </Button>
        <Button variant="secondary" onClick={() => onboardingPresentedCheck()}>
          Skip
        </Button>
      </div>
    </form>
  );
};

export default Goals;
