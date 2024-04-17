import { useSession } from "next-auth/react";
import useGetRoleStatus from "./useGetRoleStatus";
import { useEffect } from "react";

const useUpdateRoleInSession = () => {
  const { data: sessionData, update: updateSession, status } = useSession();
  const getRoleStatus = useGetRoleStatus();

  useEffect(() => {
    if (
      sessionData &&
      !getRoleStatus.data &&
      !getRoleStatus.isLoading &&
      status === "authenticated"
    ) {
      getRoleStatus.mutate(undefined, {
        onSuccess: (roleStatusResponse) => {
          if (sessionData && roleStatusResponse?.current_roles) {
            const updatedSession = {
              ...sessionData,
              authorization: {
                ...(sessionData as any).authorization,
                ...roleStatusResponse,
                role_status: roleStatusResponse.current_roles.length > 0 ? "active" : "no_purchase"
              },
            };
            updateSession(updatedSession);
          }
        },
      });
    }
  }, [
    getRoleStatus.data,
    getRoleStatus.isLoading,
    sessionData,
    status,
  ]);

  return null;
};

export default useUpdateRoleInSession;
