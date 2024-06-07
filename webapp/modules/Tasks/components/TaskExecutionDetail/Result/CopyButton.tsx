import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import Button from "components/Button";
import { FaCopy } from "react-icons/fa";
import { $generateHtmlFromNodes } from '@lexical/html';
import ToolTip from "components/Tooltip";
import { useState } from "react";



const CopyButton = ({ }) => {
    const [editor] = useLexicalComposerContext();
    const [copied, setCopied] = useState(false);

    const copyProducedTextHandler = async () => {
        let htmlContent = await new Promise<string>((res) => {

            const editorState = editor.getEditorState();
            editorState.read(() => {
                const html = $generateHtmlFromNodes(editor, null);
                res(html);
            });
        });


        try {
            const blobInput = new Blob([htmlContent], { type: 'text/html' });
            const clipboardItem = new ClipboardItem({
                'text/html': blobInput,
            });

            await navigator.clipboard.write([clipboardItem]);
            setCopied(true);
        } catch (error) {
            console.error('Failed to copy:', error);
        }

    };

    return <ToolTip
        tooltip={copied ? "copied!\n" : "copy"}
    >
        <Button
            variant="outline"
            className="flex gap-2 items-center border-gray-lighter text-gray-lighter"
            onClick={copyProducedTextHandler}
        ><FaCopy className="text-gray-dark" /> Copy
        </Button>
    </ToolTip>
}

export default CopyButton;
