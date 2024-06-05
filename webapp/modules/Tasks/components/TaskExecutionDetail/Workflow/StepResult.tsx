
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import Button from "components/Button";
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";
import useOnStepExecutionRelaunch from "modules/Tasks/hooks/useOnStepExecutionRelaunch";
import useOnSaveResultEdition from "modules/Tasks/hooks/useOnSaveResultEdition";
import TextareaAutosize from 'react-textarea-autosize';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid'
import BeatLoader from "react-spinners/BeatLoader";
import { useTranslation } from "next-i18next";
import { useState } from "react";
import ImagePreview from "../../ImagePreview";
import { render } from "@headlessui/react/dist/utils/render";



interface StepResultProps {
    stepExecutionResult: Map<string, any>[];
    sessionId: string;
    editing: boolean;
    editedResult: Map<string, any>[];
    setEditedResult: (editedResult: Map<string, any>[]) => void;

}

const StepResult: React.FC<StepResultProps> = ({
    stepExecutionResult,
    sessionId,
    editing,
    editedResult,
    setEditedResult
}) => {
    const { t } = useTranslation('dynamic');


    function renderNotEditingResultItem(key: string, value: string, resultItem: Map<string, string>) {
        // if key is 'types', return nothing
        if (key === 'types') {
            return;
        }

        // is there a key 'types' in the resultItem?
        let resultItemMap = new Map(Object.entries(resultItem));

        if (resultItemMap.has('types')) {
            let types = resultItemMap.get('types');
            let typesMap = new Map(Object.entries(types));
            if (typesMap.has(key) && typesMap.get(key) === 'image') {
                return <p className="flex-auto py-0.5 text-sm leading-5 text-gray-900">
                    <span className="font-medium text-gray-400">{key}:</span><br />
                    <ImagePreview sessionId={sessionId} filename={value} alt={value} height={800} />
                </p>;
            }
        }

        return <p className="flex-auto py-0.5 text-sm leading-5 text-gray-900">
            <span className="font-medium text-gray-400">{key}:</span><br />
            <pre style={{ whiteSpace: "pre-wrap", wordWrap: "break-word" }}>{value?.toString()}</pre>
        </p>;
    }

    function renderEditingResultItem(key: string, value: string, resultItem: Map<string, any>, resultIndex: number) {
        // if key is 'types', return nothing
        if (key === 'types') {
            return;
        }
        if (resultItem.has('types')) {
            let types = resultItem.get('types');
            let typesMap = new Map(Object.entries(types));
            if (typesMap.has(key) && typesMap.get(key) === 'image') {
                return <p className="flex-auto py-0.5 text-sm leading-5 text-gray-900">
                    <span className="font-medium text-gray-400">{key}:</span><br />
                    <ImagePreview sessionId={sessionId} filename={value} alt={value} height={800} />
                </p>;
            }
        }

        return <p className="flex-auto py-0.5 text-sm leading-5 text-gray-900">
            <span className="font-medium text-gray-400">{key}:</span><br />
            <TextareaAutosize
                className="flex-auto py-0.5 text-sm leading-5 text-gray-900 resize-none w-full"
                value={resultItem.get(key) || value?.toString()}
                onChange={event => {
                    const newResult = [...editedResult];
                    newResult[resultIndex].set(key, event.target.value);
                    setEditedResult(newResult);
                }}
            />
        </p>;
    }



    return (
        <>{
            stepExecutionResult?.map((resultItem, resultIndex) => (
                Object.entries(resultItem).map(([key, value]) => (
                    editing ?
                        renderEditingResultItem(key, value, editedResult[resultIndex], resultIndex)
                        : renderNotEditingResultItem(key, value, resultItem)
                ))
            ))
        }
        </>



    );
};

export default StepResult;