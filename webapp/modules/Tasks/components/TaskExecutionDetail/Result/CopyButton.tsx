import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import Button from "components/Button";
import { FaCopy } from "react-icons/fa";
import { $generateHtmlFromNodes } from '@lexical/html';
import ToolTip from "components/Tooltip";
import { useState } from "react";
import { useTranslation } from "next-i18next";
import useAlert from "helpers/hooks/useAlert";



const CopyButton = ({ }) => {
    const [editor] = useLexicalComposerContext();
    const [copied, setCopied] = useState(false);
    const { t } = useTranslation('dynamic');
    const { showAlert } = useAlert();

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
            showAlert({
                title: t('errorMessages.globalSnackBarMessage'),
                type: "error",
            });
        }

    };

    return <ToolTip
        tooltip={copied ? t('userTaskExecution.resultTab.copySuccess') : t('userTaskExecution.resultTab.copyButton')}
    >
        <Button
            variant="outline"
            className="flex gap-2 items-center border-gray-lighter text-gray-lighter"
            onClick={copyProducedTextHandler}
        ><FaCopy className="text-gray-dark" /> {t('userTaskExecution.resultTab.copyButton')}
        </Button>
    </ToolTip>
}

export default CopyButton;
