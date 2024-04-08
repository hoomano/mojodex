import React, { useEffect, useState } from "react";
import BeatLoader from "react-spinners/BeatLoader";
import { $getRoot, EditorState } from "lexical";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { PlainTextPlugin } from "@lexical/react/LexicalPlainTextPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import LexicalErrorBoundary from "@lexical/react/LexicalErrorBoundary";

import Toolbar from "./Toolbar";
import { EditerDraft } from "../../interface";
import { useRouter } from "next/router";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import UpdatePlugin from "./UpdatePlugin";
import useDeleteDraft from "modules/Drafts/hooks/useDeleteDraft";
import useSaveDraft from "modules/Drafts/hooks/useSaveDraft";
import useOnTaskComplete from "modules/Tasks/hooks/useOnTaskComplete";

type Props = {
  userTaskExecutionPk: number | undefined,
  task: EditerDraft;
  isLoading: boolean;
  isTask: boolean;
};

const DocumentDrafting = ({
  userTaskExecutionPk,
  task,
  isLoading = false,
  isTask = false,
}: Props) => {
  const router = useRouter();

  const [text, setText] = useState("");
  const [title, setTitle] = useState("");

  const [doneButtonText, setDoneButtonText] = useState("Done");
  const [doneButtonColor, setDoneButtonColor] = useState(
    "bg-indigo-500 hover:bg-indigo-300"
  );

  const deleteDraft = useDeleteDraft();
  const saveDraft = useSaveDraft();
  const onTaskComplete = useOnTaskComplete();

  useEffect(() => {
    setText(task.text);
    setTitle(task.title);
  }, [task]);

  const onChangeText = (state: EditorState) => {
    state.read(() => setText($getRoot().getTextContent()));
  };

  const onChangeTitle = (state: EditorState) => {
    state.read(() => setTitle($getRoot().getTextContent()));
  };

  function onSaveDraft(callback?: () => void) {
    if (task?.textPk) {
      const payload = {
        datetime: new Date().toISOString(),
        produced_text_pk: task?.textPk || null,
        production: text,
        title: title,
      };
      saveDraft.mutate(payload, {
        onSuccess: () => {
          callback && callback()
          router.push("/drafts");
          invalidateQuery([cachedAPIName.DRAFTS]);
        },
      });
    }
  }

  function onDeleteDraft() {
    if (task?.textPk) {
      deleteDraft.mutate(task.textPk, {
        onSuccess: () => {
          router.push("/drafts");
          invalidateQuery([cachedAPIName.DRAFTS]);
        },
      });
    }
  }

  function doneButtonClicked() {
    if (task?.textPk) {
      setDoneButtonText("✓");
      setDoneButtonColor("bg-gray-500");
      onSaveDraft(() => {
        onTaskComplete.mutate({
          datetime: new Date().toISOString(),
          user_task_execution_pk: userTaskExecutionPk as number,
        });
      });
    }
  }

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

  return (
    <div className="rounded-lg bg-white shadow h-screen overflow-auto grow">
      <div
        className="relative flex px-4 py-5 sm:p-6"
        style={{ wordWrap: "break-word" }}
      >
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
            placeholder={
              <div className="absolute pl-2 pointer-events-none text-gray-400 italic">
                Enter the title...
              </div>
            }
          />
          <OnChangePlugin onChange={onChangeTitle} />

          <UpdatePlugin text={task?.title || ""} />
        </LexicalComposer>

        {isTask && (
          <div className="absolute right-7 top-3">
            {isLoading ? (
              <BeatLoader color="#3763E7" />
            ) : (
              <button
                className={`${doneButtonColor} w-24 h-10 rounded-lg text-white hover:scale-105`}
                onClick={doneButtonClicked}
              >
                {doneButtonText}
              </button>
            )}
          </div>
        )}
      </div>
      <div className="bg-gray-50 px-4 py-5 sm:p-6 h-full">
        <div className="bg-white relative rounded-sm shadow-sm border border-gray-200 h-[500px] overflow-scroll">
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
              placeholder={
                <div className="absolute top-[80px] left-[10px] pointer-events-none text-gray-400 italic">
                  Enter text or select an idea/draft...
                </div>
              }
              ErrorBoundary={LexicalErrorBoundary}
            />
            <OnChangePlugin onChange={onChangeText} />
            <HistoryPlugin />
            <UpdatePlugin text={task?.text || ""} />
          </LexicalComposer>
        </div>
      </div>
    </div>
  );
};

export default DocumentDrafting;
