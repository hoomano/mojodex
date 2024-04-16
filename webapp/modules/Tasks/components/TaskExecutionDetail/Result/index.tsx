import React, { useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/router";
import BeatLoader from "react-spinners/BeatLoader";
import { $getRoot, EditorState } from "lexical";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { PlainTextPlugin } from "@lexical/react/LexicalPlainTextPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import LexicalErrorBoundary from "@lexical/react/LexicalErrorBoundary";
import { ArrowLongLeftIcon, ArrowLongRightIcon } from '@heroicons/react/20/solid';
import Button from "components/Button";
import Toolbar from "./Toolbar";
import UpdatePlugin from "./UpdatePlugin";

// import { invalidateQuery } from "services/config/queryClient";
// import cachedAPIName from "helpers/constants/cachedAPIName";
import useDeleteProducedText from "modules/ProducedTexts/hooks/useDeleteProducedText";
import useSaveDraft from "modules/ProducedTexts/hooks/useSaveProducedText";
// import useOnTaskComplete from "modules/Tasks/hooks/useOnTaskComplete";
import { EditerProducedText } from "modules/Tasks/interface";
// import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { FaCopy } from "react-icons/fa";
import ToolTip from "components/Tooltip";
import { debounce } from "helpers/method";
import { on } from "events";

type Props = {
  userTaskExecutionPk: number | undefined;
  producedText: EditerProducedText;
  isLoading: boolean;
  onGetPreviousProducedText: () => void;
  onGetNextProducedText: () => void;
  showPreviousButton: boolean;
  showNextButton: boolean;
};

const Answer = ({
  userTaskExecutionPk,
  producedText: producedText,
  isLoading = false,
  onGetPreviousProducedText,
  onGetNextProducedText,
  showPreviousButton,
  showNextButton,
}: Props) => {
  const router = useRouter();

  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [copied, setCopied] = useState(false);

  const deleteDraft = useDeleteProducedText();
  const saveDraft = useSaveDraft();

  useEffect(() => {
    setText(producedText.text);
    setTitle(producedText.title);
  }, [producedText]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const code = event.which || event.keyCode;

      let charCode = String.fromCharCode(code).toLowerCase();

      if ((event.ctrlKey || event.metaKey) && charCode === "c") {
        setTimeout(() => {
          navigator.clipboard.writeText(window.getSelection() as any);
        }, 100);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const onChangeText = async (state: EditorState) => {
    const newUpdatedText: string = await new Promise((res) => {
      state.read(() => {
        const updatedText = $getRoot().getTextContent();
        res(updatedText);
      });
    });

    if (text !== newUpdatedText) {
      setText(newUpdatedText);
      debouncedSaveDraft({ title, text: newUpdatedText });
    }
  };

  const onChangeTitle = async (state: EditorState) => {
    const updatedTitle: string = await new Promise((res) => {
      state.read(() => {
        const updatedText = $getRoot().getTextContent();
        res(updatedText);
      });
    });

    if (updatedTitle !== title) {
      setTitle(updatedTitle);
      debouncedSaveDraft({ title: updatedTitle, text });
    }
  };
  const onSaveDraft = useCallback(
    (
      updatedData: {
        title: string;
        text: string;
      } | null = null
    ) => {
      if (producedText?.producedTextPk) {
        const newText = updatedData?.text || text;
        const newTitle = updatedData?.title || title;

        if (!newText || !newTitle) return;

        const payload = {
          datetime: new Date().toISOString(),
          produced_text_pk: producedText?.producedTextPk || null,
          production: newText,
          title: newTitle,
        };

        saveDraft.mutate(payload, {
          onSuccess: () => { },
        });
      }
    },
    [producedText, title, text, userTaskExecutionPk]
  );

  const debouncedSaveDraft = useCallback(debounce(onSaveDraft, 500), [producedText]);

  const onDeleteDraft = () => {
    if (producedText?.producedTextPk) {
      deleteDraft.mutate(producedText.producedTextPk, {
        onSuccess: () => {
          router.push("/tasks");
        },
      });
    }
  };

  const copyProducedTextHandler = () => {
    navigator.clipboard.writeText(producedText?.text);
    setCopied(true);
  };

  const properNounRegex = /\*(.*?)\*/g;

  return (
    <div>
      <div className="relative py-5" style={{ wordWrap: "break-word" }}>
        <div className="bg-background-textbox rounded-md py-2">
          <LexicalComposer
            initialConfig={{
              namespace: "Title",
              theme: {
                paragraph: "mb-1",
                rtl: "text-right",
                ltr: "text-left",
              },
              editable: true,
              onError: (e) => {
                throw e;
              },
            }}
          >
            <PlainTextPlugin
              contentEditable={
                <ContentEditable className="outline-none px-2.5 resize-none overflow-hidden text-ellipsis" />
              }
              ErrorBoundary={LexicalErrorBoundary}
              placeholder={null}
            />
            <OnChangePlugin onChange={onChangeTitle} />

            <UpdatePlugin
              text={producedText?.title?.replace(properNounRegex, "$1") || ""}
            />
          </LexicalComposer>
        </div>
      </div>
      <div className="bg-background-textbox rounded-md pb-2 overflow-hidden">
        <LexicalComposer
          initialConfig={{
            namespace: "Document Content editor",
            theme: {
              paragraph: "mb-1",
              rtl: "text-right",
              ltr: "text-left",
              text: {
                bold: "font-bold",
                italic: "italic",
                underline: "underline",
                strikethrough: "line-through",
              },
            },
            onError(error) {
              throw error;
            },
          }}
        >
          <Toolbar
            onDeleteDraft={onDeleteDraft}
            onSaveDraft={onSaveDraft}
            text={text}
          />

          <RichTextPlugin
            contentEditable={
              <ContentEditable className="min-h-[450px] outline-none py-[15px] px-2.5 resize-none text-ellipsis" />
            }
            placeholder={null}
            ErrorBoundary={LexicalErrorBoundary}
          />
          <OnChangePlugin onChange={onChangeText} />
          <HistoryPlugin />
          <UpdatePlugin
            text={producedText?.text?.replace(properNounRegex, "$1") || ""}
          />
        </LexicalComposer>
      </div>
      <nav className="flex items-center justify-between border-t border-gray-200 px-4 sm:px-0">
        {showPreviousButton ? <div className="-mt-px flex w-0 flex-1">
          <a
            //href="#" => used to navigate to a certain query maybe useful ?
            onClick={onGetPreviousProducedText}
            className="inline-flex items-center border-t-2 border-transparent pr-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
          >
            <ArrowLongLeftIcon className="mr-3 h-5 w-5 text-gray-400" aria-hidden="true" />
            Previous
          </a>
        </div> : null}
        {showNextButton ? <div className="-mt-px flex w-0 flex-1 justify-end">
          <a
            // href="#"
            onClick={onGetNextProducedText}
            className="inline-flex items-center border-t-2 border-transparent pl-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
          >
            Next
            <ArrowLongRightIcon className="ml-3 h-5 w-5 text-gray-400" aria-hidden="true" />
          </a>
        </div> : null}
      </nav>
      {(
        <div className="mt-5 flex gap-2">
          {isLoading || !producedText.producedTextPk ? (
            <Button className="min-w-[100px]" variant="outline" disabled>
              <BeatLoader color="#3763E7" />
            </Button>
          ) : (
            <>
              <ToolTip
                tooltip={copied ? "copied!\n" : "copy"}
              >
                <Button
                  variant="outline"
                  className="flex gap-2 items-center border-gray-lighter text-gray-lighter"
                  onClick={copyProducedTextHandler}
                >
                  <FaCopy className="text-gray-dark" /> Copy
                </Button>
              </ToolTip>
            </>
          )}
        </div>
      )}



    </div>
  );
};

export default React.memo(Answer);
