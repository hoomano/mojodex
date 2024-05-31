import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useEffect } from "react";
import {
  $convertFromMarkdownString,
} from '@lexical/markdown';
import { MOJODEX_LEXICAL_TRANSFORMERS } from "./lexicalTransformers";

const UpdatePlugin = ({ text }: { text: string }) => {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    editor.update(() => {
      $convertFromMarkdownString(text, MOJODEX_LEXICAL_TRANSFORMERS);
    });
  }, [text]);

  return null;
};

export default UpdatePlugin;
