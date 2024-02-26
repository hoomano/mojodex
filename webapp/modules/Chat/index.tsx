import { useEffect, useContext, useState } from "react";
import Modal from "components/Modal";
import SnackBar from "components/Snackbar";
import Button from "components/Button";

import ChatAction from "modules/Chat/components//ChatAction";
import ChatBody from "modules/Chat/components//ChatBody";


import useSocket from "./hooks/useSocket";

import ChatContext from "./helpers/ChatContext";
import { socketEvents } from "helpers/constants/socket";
import { ChatContextType, ChatUsedFrom } from "./interface/context";
import useGetMessageHistory from "modules/Tasks/hooks/useGetMessageHistory";
import useChatSession from "./hooks/useChatSession";

const Chat = () => {
  const { chatState, setChatState } = useContext(
    ChatContext
  ) as ChatContextType;


  const {
    socket,
    sessionId,
    showSnackBar,
    messageSnackBar,
    chatUsedFrom,
    isNewSession,
  } = chatState;

  useSocket();
  useGetMessageHistory();

  const chatSession = useChatSession();

  useEffect(() => {
    if (isNewSession) chatSession.mutate();
  }, [isNewSession]);

  useEffect(() => {
    setChatState({
      isMobile:
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          navigator.userAgent
        ),
    });
  }, []);

  // State variable for controlling pop-up visibility
  const [showPopup, setShowPopup] = useState(false);

  // Function to show the pop-up
  const showApprovalPopup = () => {
    setShowPopup(true);
  };

  // Function to hide the pop-up
  const hideApprovalPopup = () => {
    setShowPopup(false);
  };

  const renderPopUpContent = () => {
      return (
        <>
          <div className="text-h3">👍 I'm on it</div>
          <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
            This will require some time, but don't worry, I'm on it. You can continue your work and come back later to check mine.
          </div>
        </>
      );
    
  };


  return (
    <div className="flex flex-col bg-gray-800 supports-[height:100cqh]:h-[100cqh] supports-[height:100svh]:h-[100svh]">


      <ChatBody />
      <div className="flex px-4 bg-gray-800">
        <ChatAction showPopup={showApprovalPopup} />
      </div>

      {/* Render pop-up conditionally based on state */}
      <Modal
        isOpen={showPopup}
        title="👍 I'm on it"
        footerPresent={false}
        headerPresent={false}
        widthClass="max-w-[880px] text-center"
      >
        <div className="p-[60px]">
          {renderPopUpContent()}
          <div className="mt-6">
            <Button onClick={hideApprovalPopup}>
              Ok
            </Button>
          </div>
        </div>
      </Modal>


      {showSnackBar && <SnackBar message={messageSnackBar} />}
    </div>
  );
};

export default Chat;
