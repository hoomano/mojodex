import React, { useState, useRef, useEffect, useContext } from "react";
import ChatSendButton from "./ChatSendButton";
import { useTranslation } from "react-i18next";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";

interface ChatAcceptToolButtonsType {
    onApproveTool: () => void;
    onRejectTool: () => void;
}

const ChatAcceptToolButtons = ({
    onApproveTool,
    onRejectTool,
}: ChatAcceptToolButtonsType) => {
    const { t } = useTranslation("dynamic");

    const { setGlobalState } = useContext(globalContext) as GlobalContextType;


    // Render the component
    // a line with 2 buttons: yes and no
    return (
        <div className="flex justify-center space-x-4 w-full my-2">
            <button className="flex-grow px-4 py-2 bg-gray-lighter text-white rounded" onClick={() => onRejectTool()}>{t("validationWidget.noButton")}</button>
            <button className="flex-grow mr-2 px-4 py-2 bg-primary-main text-white rounded" onClick={() => onApproveTool()}>{t("validationWidget.okButton")}</button>
        </div>
    );
};

export default ChatAcceptToolButtons;
