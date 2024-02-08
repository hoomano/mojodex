import { useMutation } from "@tanstack/react-query";
import { forgotPassword } from "services/auth";

const useForgotPassword = () => useMutation(forgotPassword);

export default useForgotPassword;
