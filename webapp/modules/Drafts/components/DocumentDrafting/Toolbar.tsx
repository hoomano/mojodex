import clsx from "clsx";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useCallback, useEffect, useState } from "react";
import ShareButton from "components/ShareableDraft/ShareButton";
import { mergeRegister } from "@lexical/utils";
import {
  $getSelection,
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  FORMAT_ELEMENT_COMMAND,
  UNDO_COMMAND,
  REDO_COMMAND,
} from "lexical";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import {
  faAlignLeft,
  faAlignCenter,
  faAlignRight,
  faBold,
  faItalic,
  faRotateLeft,
  faRotateRight,
  faStrikethrough,
  faUnderline,
  faAlignJustify,
  faSave,
  faTrashCan,
} from "@fortawesome/free-solid-svg-icons";

type Props = {
  onSaveDraft: Function;
  onDeleteDraft: Function;
  text: string;
};

const Toolbar = ({ onSaveDraft, onDeleteDraft, text }: Props) => {
  const [editor] = useLexicalComposerContext();
  const [isBold, setIsBold] = useState(false);
  const [isItalic, setIsItalic] = useState(false);
  const [isStrikethrough, setIsStrikethrough] = useState(false);
  const [isUnderline, setIsUnderline] = useState(false);

  const updateToolbar = useCallback(() => {
    const selection = $getSelection();

    if ($isRangeSelection(selection)) {
      setIsBold(selection.hasFormat("bold"));
      setIsItalic(selection.hasFormat("italic"));
      setIsStrikethrough(selection.hasFormat("strikethrough"));
      setIsUnderline(selection.hasFormat("underline"));
    }
  }, [editor]);

  useEffect(() => {
    mergeRegister(
      editor.registerUpdateListener(({ editorState }) => {
        editorState.read(() => {
          updateToolbar();
        });
      })
    );
  }, [updateToolbar, editor]);

  return (
    <div className="sticky top-0 left-0 shadow bottom-8 min-w-52 h-10 px-2 py-2 bg-[#1b2733] mb-4 space-x-2 flex items-center">
      <button
        className={clsx(
          "px-1 hover:bg-gray-700 transition-colors duration-100 ease-in",
          isBold ? "bg-gray-700" : "bg-transparent"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, "bold");
        }}
      >
        <FontAwesomeIcon icon={faBold} className="text-white w-3.5 h-3.5" />
      </button>
      <button
        className={clsx(
          "px-1 hover:bg-gray-700 transition-colors duration-100 ease-in",
          isStrikethrough ? "bg-gray-700" : "bg-transparent"
        )}
        onClick={() =>
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, "strikethrough")
        }
      >
        <FontAwesomeIcon
          icon={faStrikethrough}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 hover:bg-gray-700 transition-colors duration-100 ease-in",
          isItalic ? "bg-gray-700" : "bg-transparent"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, "italic");
        }}
      >
        <FontAwesomeIcon icon={faItalic} className="text-white w-3.5 h-3.5" />
      </button>
      <button
        className={clsx(
          "px-1 hover:bg-gray-700 transition-colors duration-100 ease-in",
          isUnderline ? "bg-gray-700" : "bg-transparent"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_TEXT_COMMAND, "underline");
        }}
      >
        <FontAwesomeIcon
          icon={faUnderline}
          className="text-white w-3.5 h-3.5"
        />
      </button>

      <span className="w-[1px] bg-gray-600 block h-full"></span>

      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, "left");
        }}
      >
        <FontAwesomeIcon
          icon={faAlignLeft}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, "center");
        }}
      >
        <FontAwesomeIcon
          icon={faAlignCenter}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, "right");
        }}
      >
        <FontAwesomeIcon
          icon={faAlignRight}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => {
          editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, "justify");
        }}
      >
        <FontAwesomeIcon
          icon={faAlignJustify}
          className="text-white w-3.5 h-3.5"
        />
      </button>

      <span className="w-[1px] bg-gray-600 block h-full"></span>

      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => editor.dispatchCommand(UNDO_COMMAND, undefined)}
      >
        <FontAwesomeIcon
          icon={faRotateLeft}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => editor.dispatchCommand(REDO_COMMAND, undefined)}
      >
        <FontAwesomeIcon
          icon={faRotateRight}
          className="text-white w-3.5 h-3.5"
        />
      </button>
      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => onSaveDraft()}
        type="button"
        title="Save the draft"
      >
        <FontAwesomeIcon icon={faSave} className="text-white w-3.5 h-3.5" />
      </button>

      <button
        className={clsx(
          "px-1 bg-transparent hover:bg-gray-700 transition-colors duration-100 ease-in"
        )}
        onClick={() => onDeleteDraft()}
        type="button"
        title="Delete the draft"
      >
        <FontAwesomeIcon icon={faTrashCan} className="text-white w-3.5 h-3.5" />
      </button>

      <ShareButton message={text} />
    </div>
  );
};

export default Toolbar;
