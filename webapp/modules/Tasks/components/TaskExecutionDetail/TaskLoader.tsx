import Loader from "components/Loader";
import React from "react";

const TaskLoader = () => {
  return (
    <div className="w-[100%] h-[100%] flex flex-col items-center justify-center">
      <img src="/images/writing.png" className="h-8 w-8 bg-white" />
      <div className="text-h2 font-semibold text-center py-[10px]">
        Generating an answer..
      </div>
      <div className="text-h5 text-gray-lighter">Please give us a moment</div>
      <Loader />
    </div>
  );
};

export default TaskLoader;
