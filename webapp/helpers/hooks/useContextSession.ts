import { useContext } from "react";
import globalContext, { GlobalContextType } from "../GlobalContext";

const useContextSession = () => {
  const { globalState } = useContext(globalContext) as GlobalContextType;
  const { session } = globalState;
  return session;
};

export default useContextSession;
