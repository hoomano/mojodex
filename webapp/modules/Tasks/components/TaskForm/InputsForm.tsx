import { TaskJsonInput, InputArrayProps, TaskJsonInputType } from "modules/Tasks/interface";
import { Dispatch, SetStateAction } from "react";
import DropDownList from "./DropDownList";
import ImageArea from "./ImageArea";
import Textarea from "./TextArea";
import MultipleImagesArea from "./MultipleImagesArea";
import AudioFile from "./AudioFile";

interface InputsFormProps {
    jsonInputs: TaskJsonInput[];
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
    sessionId: string;
}

const InputsForm = ({ jsonInputs, setInputArray, sessionId }: InputsFormProps) => {

    return <div className="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">

        {jsonInputs.map((input) => {

            switch (input.type) {
                case TaskJsonInputType.MULTIPLE_IMAGES:
                    return (
                        <MultipleImagesArea
                            key={input.input_name}
                            jsonInput={input}
                            setInputArray={setInputArray}
                            sessionId={sessionId}
                        />
                    );
                case TaskJsonInputType.IMAGE:
                    return (
                        <ImageArea
                            key={input.input_name}
                            jsonInput={input}
                            setInputArray={setInputArray}
                            sessionId={sessionId}
                        />
                    );
                case TaskJsonInputType.AUDIO_FILE:
                    return (
                        <AudioFile
                            key={input.input_name}
                            jsonInput={input}
                            setInputArray={setInputArray}
                        />
                    );
                case TaskJsonInputType.DROP_DOWN_LIST:
                    return (
                        <DropDownList
                            key={input.input_name}
                            jsonInput={input}
                            setInputArray={setInputArray}
                        />
                    );
                default:
                    return (
                        <Textarea
                            key={input.input_name}
                            jsonInput={input}
                            setInputArray={setInputArray}
                        />
                    );
            }
        })}
    </div>
}

export default InputsForm;