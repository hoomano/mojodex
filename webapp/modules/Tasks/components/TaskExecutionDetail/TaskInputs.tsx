import { InputArrayProps, TaskJsonInput, TaskJsonInputType } from "modules/Tasks/interface";
import React, { FunctionComponent, useState } from "react";

import Button from "components/Button";
import InputsForm from "../TaskForm/InputsForm";
import ImagePreview from "../ImagePreview";
import useOnWorkflowRestart from "modules/Tasks/hooks/useOnWorkflowRestart";
import { useTranslation } from "next-i18next";
import useAlert from "helpers/hooks/useAlert";
import { FaFileAudio, FaFileVideo } from "react-icons/fa";

interface TaskInputsProps {
    user_task_execution_pk: number;
    inputs: TaskJsonInput[];
    sessionId: string;
    editable: boolean;
    onCancelEdition: () => void;
    onSaveAndRestart: () => void;
}



const TaskInputs: FunctionComponent<TaskInputsProps> = ({ user_task_execution_pk, inputs, sessionId, editable, onCancelEdition, onSaveAndRestart }) => {
    const onWorkflowRestart = useOnWorkflowRestart();
    const { t } = useTranslation('dynamic');
    const { showAlert } = useAlert();
    
    const [inputArray, setInputArray] = useState<InputArrayProps[]>(inputs.map((input) => ({
        input_name: input.input_name,
        input_value: input.value || '', // Add a default value of an empty string if input.value is undefined
        })));
    // For now, restart can only be done on workflows, not instruct tasks
    const restartWorkflow = () => {
        onWorkflowRestart.mutate({
            user_task_execution_pk: user_task_execution_pk,
            inputs: inputArray,
        }, {
            onSuccess: () => {
                // edit inputs using inputArray
                // for each name in inputArray, find the corresponding input in inputs and update its value
                inputArray.forEach((input) => {
                    const inputToUpdate = inputs.find((i) => i.input_name === input.input_name);
                    if (inputToUpdate) {
                        if (input.input_value instanceof File) {
                            inputToUpdate.value = input.input_value.name;
                        } else {
                            inputToUpdate.value = input.input_value as string;
                        }
                    }
                });
                onSaveAndRestart();
            },
            onError: (error) => {
                showAlert({
                    title: t('userTaskExecution.inputsTab.restartError'),
                    type: "error",
                });
            }
        });  
    }

    return (
        <div className="p-[30px] w-full">
            {editable ?
                <div className=" pt-2">
                    <div className="pb-4">
                        <InputsForm
                            jsonInputs={inputs}
                            setInputArray={setInputArray}
                            sessionId={sessionId}
                        />
                    </div>
                    <div className="flex justify-end">
                        <Button
                            variant="outline"
                            size="middle"
                            onClick={onCancelEdition}
                            className="mr-2"
                        >
                            {t("userTaskExecution.inputsTab.cancelEditionButton")}
                        </Button>

                        <Button variant="primary" size="middle" onClick={restartWorkflow}>
                            {t("userTaskExecution.inputsTab.saveEditionButton")}
                        </Button>
                    </div>
                </div>
                : <ul role="list" className="space-y-6 w-full">
                    {inputs?.map((input, index) => { 
                        switch (input.type) {
                            case TaskJsonInputType.MULTIPLE_IMAGES:
                                return <div>
                                    <h1>{input.input_name}</h1>
                                    {(input.value.map((image: string, index: number) => {
                                    return (
                                        <div key={index} className="flex flex-col">
                                            <ImagePreview sessionId={sessionId} filename={image} alt={input.description_for_user} />
                                        </div>
                                    )
                                }))}</div>
                            case TaskJsonInputType.IMAGE:
                                return <>
                                    <h1>{input.input_name}</h1>
                                    <p>{input.value}</p>
                                    <ImagePreview sessionId={sessionId} filename={input.value!} alt={input.description_for_user} />
                                </>
                            case TaskJsonInputType.AUDIO_FILE:
                                return <>
                                    <h1>{input.input_name}</h1>
                                    <p>{input.value}</p>
                                    <FaFileAudio className="w-6 h-6" />
                                </>
                            case TaskJsonInputType.VIDEO:
                                return <>
                                    <h1>{input.input_name}</h1>
                                    <p>{input.value}</p>
                                    <FaFileVideo className="w-6 h-6" />
                                </>
                            default:
                                return <>
                                    <h1>{input.input_name}</h1>
                                    <p className="text-sm text-justify">
                                        {input.value?.split('\n').map((line: string, index: number) => (
                                            <React.Fragment key={index}>
                                                {line}
                                                <br />
                                            </React.Fragment>
                                        ))}
                                    </p>
                                </>
                        
                        }
                    })}
                </ul>}
        </div>
    );
};

export default TaskInputs;