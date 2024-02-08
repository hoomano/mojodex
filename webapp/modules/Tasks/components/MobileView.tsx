import React from "react";
import { useRouter } from "next/router";
import Button from "components/Button";

const MobileView = () => {
  const router = useRouter();

  return (
    <div className="text-center mt-[170px]">
      <img src="/images/writing.png" className="h-8 w-8 m-auto" />
      <div className="text-h2 font-semibold my-[10px]">
        Generating an answer...
      </div>
      <div className="text-h5 text-gray-lighter">Look at the result</div>
      <img src="/images/laptop.png" className="m-auto pt-[60px]" />
      <div className="text-h2 font-semibold">on a laptop</div>
      <Button
        variant="outline"
        className="flex gap-2 items-center !border-gray-lighter !text-gray-lighter m-auto !mt-[60px] cursor-pointer"
        onClick={() => router.push("/tasks")}
      >
        <img src="/images/exit.png" /> Back to tasks
      </Button>
    </div>
  );
};

export default MobileView;
