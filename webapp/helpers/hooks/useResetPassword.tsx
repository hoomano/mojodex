import { useMutation } from "@tanstack/react-query";
import { resetPassword } from "services/auth";

const useResetPassword = () => useMutation(resetPassword);

export default useResetPassword;
