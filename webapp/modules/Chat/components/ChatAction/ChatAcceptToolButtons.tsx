import React, { useState, useRef, useEffect, useContext } from "react";
import ChatSendButton from "./ChatSendButton";

import globalContext, { GlobalContextType } from "helpers/GlobalContext";

interface ChatAcceptToolButtonsType {
    onApproveTool: () => void;
    onRejectTool: () => void;
}

const ChatAcceptToolButtons = ({
    onApproveTool,
    onRejectTool,
}: ChatAcceptToolButtonsType) => {
   

    const { setGlobalState } = useContext(globalContext) as GlobalContextType;


    // Render the component
    // a line with 2 buttons: yes and no
    return (
        <div className="flex justify-center space-x-4">
            <button className="mr-2 px-4 py-2 bg-green-500 text-white rounded" onClick={() => onApproveTool()}>Yes</button>
            <button className="px-4 py-2 bg-red-500 text-white rounded" onClick={() => onRejectTool()}>No</button>
        </div>
    );
};

export default ChatAcceptToolButtons;
