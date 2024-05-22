import { InputArrayProps, TaskJsonInput } from "modules/Tasks/interface";
import React, { FunctionComponent, useState } from "react";

import Button from "components/Button";
import InputsForm from "../TaskForm/InputsForm";
import ImagePreview from "../ImagePreview";
import useOnWorkflowRestart from "modules/Tasks/hooks/useOnWorkflowRestart";
import { useTranslation } from "next-i18next";

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
                alert(t("userTaskExecution.inputsTab.restartError"));
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
                    {inputs?.map((input, index) => (
                        <li key={index} className="relative flex flex-col">
                            <h1 className="text-xl font-bold mb-2">{input.description_for_user}</h1>

                            {input.type === "image" ? (
                                <>
                                    <p>{input.value}</p>
                                    <ImagePreview sessionId={sessionId} filename={input.value!} alt={input.description_for_user} />
                                </>
                            ) : (
                                <>

                                    <p className="text-sm text-justify">
                                        {input.value?.split('\n').map((line, index) => (
                                            <React.Fragment key={index}>
                                                {line}
                                                <br />
                                            </React.Fragment>
                                        ))}
                                    </p>
                                </>
                            )}
                        </li>
                    ))}
                </ul>}
        </div>
    );
};

export default TaskInputs;