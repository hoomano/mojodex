import { TaskJsonInput } from "modules/Tasks/interface";
import React, { FunctionComponent } from "react";

import Button from "components/Button";
import InputsForm from "../TaskForm/inputsForm";
import ImagePreview from "../imagePreview";
import useOnWorkflowRestart from "modules/Tasks/hooks/useOnWorkflowRestart";

interface TaskInputsProps {
    inputs: TaskJsonInput[];
    sessionId: string;
    editable: boolean;
    onCancelEdition?: () => void;
    onSaveAndRestart?: () => void;
}



const TaskInputs: FunctionComponent<TaskInputsProps> = ({ inputs, sessionId, editable, onCancelEdition, onSaveAndRestart }) => {
    const onWorkflowRestart = useOnWorkflowRestart();
    // For now, restart can only be done on workflows, not instruct tasks
    const restartWorkflow = () => {
        onWorkflowRestart.mutate({
            user_workflow_step_execution_pk: user_task_execution_pk,
            inputs: inputs
        }, {
            onSuccess: (data) => {
                console.log(data);
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
                            setInputArray={() => { }}
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

                        <Button variant="primary" size="middle" onClick={onSaveAndRestart}>
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