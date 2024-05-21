import { InputArrayProps, TaskJsonInput } from "modules/Tasks/interface";
import React, { FunctionComponent, useState } from "react";

import Button from "components/Button";
import InputsForm from "../TaskForm/inputsForm";
import ImagePreview from "../imagePreview";
import useOnWorkflowRestart from "modules/Tasks/hooks/useOnWorkflowRestart";

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
    const [inputArray, setInputArray] = useState<InputArrayProps[]>(inputs.map((input) => ({
        input_name: input.input_name,
        input_value: input.value || '', // Add a default value of an empty string if input.value is undefined
        })));
    // For now, restart can only be done on workflows, not instruct tasks
    const restartWorkflow = () => {
        // edit inputs using inputArray
        // for each name in inputArray, find the corresponding input in inputs and update its value
        inputArray.forEach((input) => {
            const inputToUpdate = inputs.find((i) => i.input_name === input.input_name);
            if (inputToUpdate) {
                if(input.input_value instanceof File) {
                    inputToUpdate.value = input.input_value.name;
                } else {
                    inputToUpdate.value = input.input_value as string;
                }
            }
        });

        onWorkflowRestart.mutate({
            user_task_execution_pk: user_task_execution_pk,
            inputs: inputArray,
        }, {
            onSuccess: (data) => {
                onSaveAndRestart(); // todo: update current tasks inputs for display
            },
            onError: (error) => {
                console.log("Error saving result edition", error);
                // todo: manage error message
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
                            Cancel
                        </Button>

                        <Button variant="primary" size="middle" onClick={restartWorkflow}>
                            Save and restart
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