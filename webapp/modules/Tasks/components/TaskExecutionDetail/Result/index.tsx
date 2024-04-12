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

import Button from "components/Button";
import Toolbar from "./Toolbar";
import UpdatePlugin from "./UpdatePlugin";

// import { invalidateQuery } from "services/config/queryClient";
// import cachedAPIName from "helpers/constants/cachedAPIName";
import useDeleteProducedText from "modules/ProducedTexts/hooks/useDeleteProducedText";
import useSaveDraft from "modules/ProducedTexts/hooks/useSaveProducedText";
// import useOnTaskComplete from "modules/Tasks/hooks/useOnTaskComplete";
import { EditerDraft } from "modules/Tasks/interface";
// import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { FaCopy } from "react-icons/fa";
import ToolTip from "components/Tooltip";
import { debounce } from "helpers/method";

type Props = {
  userTaskExecutionPk: number | undefined;
  task: EditerDraft;
  isLoading: boolean;
  isTask: boolean;
};

const Answer = ({
  userTaskExecutionPk,
  task,
  isLoading = false,
  isTask = false,
}: Props) => {
  const router = useRouter();

  // const { setGlobalState } = useContext(globalContext) as GlobalContextType;

  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [copied, setCopied] = useState(false);

  const deleteDraft = useDeleteProducedText();
  const saveDraft = useSaveDraft();
  // const onTaskComplete = useOnTaskComplete();

  useEffect(() => {
    setText(task.text);
    setTitle(task.title);
  }, [task]);

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
      if (task?.textPk) {
        const newText = updatedData?.text || text;
        const newTitle = updatedData?.title || title;

        if (!newText || !newTitle) return;

        const payload = {
          datetime: new Date().toISOString(),
          produced_text_pk: task?.textPk || null,
          production: newText,
          title: newTitle,
        };

        saveDraft.mutate(payload, {
          onSuccess: () => { },
        });
      }
    },
    [task, title, text, userTaskExecutionPk]
  );

  const debouncedSaveDraft = useCallback(debounce(onSaveDraft, 500), [task]);

  const onDeleteDraft = () => {
    if (task?.textPk) {
      deleteDraft.mutate(task.textPk, {
        onSuccess: () => {
          router.push("/tasks");
        },
      });
    }
  };

  // const onSaveAndSuggestFollowUp = () => {
  //   onSaveDraft();
  //   onTaskComplete.mutate(
  //     {
  //       datetime: new Date().toISOString(),
  //       user_task_execution_pk: userTaskExecutionPk as number,
  //     },
  //     {
  //       onSuccess: () => {
  //         router.push("/tasks");
  //         setGlobalState({ showTaskDoneModal: true });
  //       },
  //     }
  //   );
  // };

  const copyProducedTextHandler = () => {
    navigator.clipboard.writeText(task?.text);
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
              text={task?.title?.replace(properNounRegex, "$1") || ""}
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
            text={task?.text?.replace(properNounRegex, "$1") || ""}
          />
        </LexicalComposer>
      </div>
      {isTask && (
        <div className="mt-5 flex gap-2">
          {isLoading || !task.title ? (
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
              {/* <Button onClick={onSaveAndSuggestFollowUp}>
                Suggest Follow-up
              </Button> */}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default React.memo(Answer);
