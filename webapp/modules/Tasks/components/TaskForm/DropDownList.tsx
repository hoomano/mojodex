import { InputArrayProps, TaskJsonInput } from "modules/Tasks/interface";
import React, { Dispatch, SetStateAction, useRef } from "react";

interface Props {
    jsonInput: TaskJsonInput;
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
}

const DropDownList = ({ jsonInput, setInputArray }: Props) => {
    const { input_name, placeholder, description_for_user, possible_values } = jsonInput;
    
    const selectedValue = useRef<string | undefined>(undefined);

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        selectedValue.current = e.target.value;
        setInputArray((prev) => {
            const index = prev.findIndex((input) => input.input_name === input_name);
            if (index !== -1) {
                prev[index].input_value = e.target.value;
            } else {
                prev.push({ input_name, input_value: e.target.value });
            }
            return [...prev];
        });
    };

    return (
        <div className="col-span-full" key={input_name}>
            <label htmlFor={input_name} className="text-subtitle3">
                {description_for_user}
            </label>
            <div className="flex items-start space-x-4">
                <div className="min-w-0 flex-1">
                    <div className="rounded-lg ring-1 ring-inset ring-gray-lighter focus-within:ring-2 focus-within:ring-primary-main">
                        <select
                            className="block overflow-auto resize-none w-full border-0 bg-transparent py-1.5 text-gray-dark placeholder:text-gray-dark focus:ring-0 sm:text-sm sm:leading-6"

                            id={input_name}
                            name={input_name}
                            onChange={handleChange}
                            defaultValue={jsonInput.value}
                        >
                            <option value="" disabled selected>
                                {placeholder}
                            </option>
                            {possible_values?.map((value) => (
                                <option key={value.value} value={value.value}>
                                    {value.displayed_text}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>
        </div>
    );

};

export default DropDownList;