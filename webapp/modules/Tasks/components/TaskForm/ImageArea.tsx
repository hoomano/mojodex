import React, { Dispatch, SetStateAction, useState, useRef } from 'react';
import { InputArrayProps, TaskJsonInput } from 'modules/Tasks/interface';

interface ImageAreaProps {
    jsonInput: TaskJsonInput;
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
}

const ImageArea = ({ jsonInput, setInputArray }: ImageAreaProps) => {
    const { input_name, description_for_user } = jsonInput;
    const [imagePreview, setImagePreview] = useState<string | ArrayBuffer | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
                setInputArray((prev) => {
                    const updatedInputArray = [...prev];
                    const existingIndex = updatedInputArray.findIndex(
                        (input) => input.input_name === input_name
                    );
                    if (existingIndex === -1) {
                        updatedInputArray.push({
                            input_name,
                            input_value: reader.result as string,
                        });
                    } else {
                        updatedInputArray[existingIndex] = {
                            input_name,
                            input_value: reader.result as string,
                        };
                    }
                    return updatedInputArray;
                });
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="col-span-full" key={input_name}>
            <label htmlFor={input_name} className="text-subtitle3">
                {description_for_user}
            </label>
            <div className="flex items-start space-x-4">
                <div className="min-w-0 flex-1">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleImageChange}
                        className="hidden"
                    />
                    <button
                        type="button"
                        className="rounded-lg ring-1 ring-inset ring-gray-lighter focus:ring-2 focus:ring-primary-main"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        {imagePreview ? (
                            <img src={imagePreview as string} alt="Preview" className="rounded-lg w-full" />
                        ) : (
                            'Upload Image'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ImageArea;