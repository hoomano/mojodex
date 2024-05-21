import React, { Dispatch, SetStateAction, useState, useRef } from 'react';
import { InputArrayProps, TaskJsonInput } from 'modules/Tasks/interface';
import Button from 'components/Button';
import ImagePreview from '../imagePreview';

interface ImageAreaProps {
    jsonInput: TaskJsonInput;
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
    sessionId: string;
}

const ImageArea = ({ jsonInput, setInputArray, sessionId }: ImageAreaProps) => {
    const { input_name, description_for_user } = jsonInput;
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;
        
        if (file && file.type.startsWith('image/')) {
            setImagePreview(URL.createObjectURL(file));
            setInputArray((prev) => {
                const updatedInputArray = [...prev];
                const existingIndex = updatedInputArray.findIndex(
                    (input) => input.input_name === input_name
                );
                if (existingIndex === -1) {
                    updatedInputArray.push({
                        input_name,
                        input_value: file,
                    });
                } else {
                    updatedInputArray[existingIndex] = {
                        input_name,
                        input_value: file,
                    };
                }
                return updatedInputArray;
            });
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
                    <Button
                        variant="secondary"
                        className="min-w-[83px]"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        {imagePreview ? (
                            <img src={imagePreview as string} alt="Preview" style={{ maxWidth: '300px' }}  className="rounded-lg w-full" />
                        ) : jsonInput.value ? <ImagePreview sessionId={sessionId} filename={jsonInput.value!} alt={jsonInput.description_for_user} /> : (
                            'Upload Image' //todo: i18n
                        )
                        }
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ImageArea;