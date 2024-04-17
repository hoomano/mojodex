import { useMutation } from "@tanstack/react-query";
import { getRoleStatus } from "services/payment";

const useGetRoleStatus = () => useMutation(getRoleStatus);

export default useGetRoleStatus;
