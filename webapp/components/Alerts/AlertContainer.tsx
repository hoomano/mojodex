import React, { useContext, useEffect } from "react";
import Alerts from "components/Alerts";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";

const AlertContainer = () => {
  const {
    globalState: { alert },
    setGlobalState,
  } = useContext(globalContext) as GlobalContextType;

  const onClose = () =>
    alert && setGlobalState({ alert: { ...alert, show: false } });

  useEffect(() => {
    let timer: any;
    if (alert && alert.show) {
      timer = setTimeout(onClose, 5000);
    }
    return () => clearTimeout(timer);
  }, [alert?.show]);

  return (
    <Alerts
      title={alert?.title}
      type={alert?.type || "primary"}
      show={alert?.show || false}
      onClose={onClose}
    />
  );
};

export default AlertContainer;
