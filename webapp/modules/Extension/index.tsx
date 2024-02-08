import React from "react";

const Extension = () => {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="p-[60px]">
        <div>🎉Welcome!</div>
        <div className="mb-10">You successfully logged in</div>

        <div>Now, 3 little steps:</div>
        <div className="pl-2"> 1. Close this pop-up</div>
        <div className="pl-2"> 2. Close the Chrome Extension</div>
        <div className="pl-2"> 3. Re-open the Mojodex Chrome Extension</div>
      </div>
    </div>
  );
};

export default Extension;
