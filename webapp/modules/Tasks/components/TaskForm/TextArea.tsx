import { InputArrayProps, TaskJsonInput } from "modules/Tasks/interface";
import React, { Dispatch, SetStateAction, useRef } from "react";

interface Props {
  jsonInput: TaskJsonInput;
  setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
}

const Textarea = ({ jsonInput, setInputArray }: Props) => {
  const { input_name, placeholder, description_for_user } = jsonInput;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleChangeInput = () => {
    if (textareaRef.current) {
      const inputName = textareaRef.current.name;
      const inputValue = textareaRef.current.value;

      setInputArray((prev) => {
        let updatedInputArray = [...prev];

        const existingIndex = updatedInputArray.findIndex(
          (line) => line.input_name === inputName
        );
        if (inputValue != "") {
          if (existingIndex === -1) {
            updatedInputArray.push({
              input_name: inputName,
              input_value: inputValue,
            });
          } else {
            updatedInputArray[existingIndex] = {
              input_name: inputName,
              input_value: inputValue,
            };
          }
        } else {
          if (existingIndex !== -1) {
            updatedInputArray.splice(existingIndex, 1);
          }
        }
        

        return updatedInputArray;
      });
    }
  };

  const handleTextareaInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"; // Reset height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="col-span-full" key={input_name}>
      <label htmlFor={input_name} className="text-subtitle3">
        {description_for_user}
      </label>
      <div className="flex items-start space-x-4">
        <div className="min-w-0 flex-1">
          <div className="rounded-lg ring-1 ring-inset ring-gray-lighter focus-within:ring-2 focus-within:ring-primary-main">
            <textarea
              ref={textareaRef}
              rows={5}
              name={input_name}
              className="block overflow-auto resize-none w-full border-0 bg-transparent py-1.5 text-gray-dark placeholder:text-gray-dark focus:ring-0 sm:text-sm sm:leading-6"
              placeholder={placeholder}
              onBlur={handleChangeInput}
              onInput={handleTextareaInput}
              defaultValue={jsonInput.value}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Textarea;
