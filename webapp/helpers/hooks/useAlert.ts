import { Alert } from "components/Alerts";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { useContext } from "react";

const useAlert = () => {
  const { setGlobalState } = useContext(globalContext) as GlobalContextType;
  const showAlert = (alert: Omit<Alert, "show">) =>
    setGlobalState({ alert: { ...alert, show: true } });
  return { showAlert };
};

export default useAlert;
