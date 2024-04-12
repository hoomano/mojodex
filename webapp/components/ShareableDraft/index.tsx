import React, { useRef, useState } from "react";
import ToolTip from "../Tooltip";
import { FaCopy, FaCheck } from "react-icons/fa"; // Import the send icon from the Font Awesome library
import ShareButton from "./ShareButton";
import { MessageType } from "modules/Chat/interface";

interface ShareableDraftType {
  message: MessageType;
  isMobile?: boolean;
}

const ShareableDraft = ({ message, isMobile }: ShareableDraftType) => {
  const textToCopy: any = useRef(null);
  const [copied, setCopied] = useState(false);

  /// Manage \n for multilines
  const lines = message?.question?.split("\n") || [];
  const answerWithBreaks = lines.map((line, index) => {
    return (
      <span key={index}>
        {line}
        <br />
      </span>
    );
  });

  const copyMessage = () => {
    // Replace newline characters with line break elements
    if (isMobile) {
      var text = textToCopy?.current?.innerHTML;
      text = text.replaceAll("<span> ", "");
      text = text.replaceAll("<span>", "");
      text = text.replaceAll("</span>", "");
      text = text.replaceAll("<br>", "\n");
      text = text.replaceAll("&lt;", "<");
      text = text.replaceAll("&gt;", ">");
      text = text + "\n\nAssisted by Mojodex (https://hoomano.com/mojodex)";
      navigator.clipboard.writeText(text);
      setCopied(true);
    } else {
      var html = textToCopy.current.innerHTML;

      // Add "<br> <p>Assisted by <a href='https://hoomano.com/mojodex'>Mojodex</a></p>"
      html =
        html +
        "<br> <p>Assisted by <a href='https://hoomano.com/mojodex'>Mojodex</a></p>";
      navigator.clipboard.writeText(html).then(function () {
        setCopied(true);
      });
    }
  };

  return (
    <div className="flex flex-grow flex-col justify-between">
      <div className="flex flex-grow flex-row justify-between">
        <div className="flex flex-col flex-grow mt-1 text-sm text-white">
          <div className="text-xs text-gray-400 mr-2">DOCUMENT</div>
        </div>

        <div className="flex-none mr-3">
          <ShareButton message={message.produced_text} />
        </div>
        <div className="flex-none mt-1 mr-1">
          {!isMobile ? (
            <ToolTip tooltip={copied ? "copied!" : "copy"}>
              {copied ? (
                <FaCheck
                  className="text-gray-500 hover:text-white"
                  onClick={copyMessage}
                />
              ) : (
                <FaCopy
                  className="text-gray-500 hover:text-white hover:cursor-pointer"
                  onClick={copyMessage}
                />
              )}
            </ToolTip>
          ) : copied ? (
            <FaCheck
              className="text-gray-500 hover:text-white hover:cursor-pointer"
              onClick={copyMessage}
            />
          ) : (
            <FaCopy
              className="text-gray-500 hover:text-white hover:cursor-pointer"
              onClick={copyMessage}
            />
          )}
        </div>
      </div>
      <div className="flex flex-grow flex-row justify-between">
        <div className="flex flex-col flex-grow mt-1 text-sm text-white">
          <p ref={textToCopy} className="mt-2">
            {answerWithBreaks}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ShareableDraft;
