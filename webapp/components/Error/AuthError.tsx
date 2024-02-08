import React from "react";
import { IoMdClose } from "react-icons/io";

interface AuthErrorType {
  title: string;
  onclickHandler: any;
}

const AuthError = ({ title, onclickHandler }: AuthErrorType) => {
  return (
    <>
      <div className="flex items-center gap-3 justify-between bg-[#ffebe9] border border-[rgba(255,129,130,0.4)] py-3 px-4 rounded-md">
        <div className="">{title}</div>
        <IoMdClose className="text-[20px] text-[#d1242f] cursor-pointer" onClick={onclickHandler} />
      </div>
    </>
  );
};

export default AuthError;
