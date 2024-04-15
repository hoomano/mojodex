import { TaskJsonInput } from "modules/Tasks/interface";
import React, { FunctionComponent } from "react";



interface TaskInputsProps {
    inputs: TaskJsonInput[];
}

const TaskInputs: FunctionComponent<TaskInputsProps> = ({ inputs }) => {
    return (
        <div className="p-[30px] w-full">
            <ul role="list" className="space-y-6 w-full">
                {inputs?.map((input, index) => (
                    <li key={index} className="relative flex flex-col">
                        <h1 className="text-xl font-bold mb-2">{input.description_for_user}</h1>
                        <p className="text-sm text-justify">
                            {input.value?.split('\n').map((line, index) => (
                                <React.Fragment key={index}>
                                    {line}
                                    <br />
                                </React.Fragment>
                            ))}
                        </p>
                    </li>
                ))}
            </ul>

        </div>
    );
};

export default TaskInputs;
