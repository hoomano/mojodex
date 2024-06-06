import React, { Dispatch, SetStateAction, useState, useRef } from 'react';
import { InputArrayProps, TaskJsonInput } from 'modules/Tasks/interface';
import Button from 'components/Button';
import ImagePreview from '../ImagePreview';
import { useTranslation } from "next-i18next";

interface MultipleImagesAreaProps {
    jsonInput: TaskJsonInput;
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
    sessionId: string;
}


const MultipleImagesArea = ({ jsonInput, setInputArray, sessionId }: MultipleImagesAreaProps) => {
    const { input_name, description_for_user } = jsonInput;
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { t } = useTranslation('dynamic');

    const newImage = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;

        if (file && file.type.startsWith('image/')) {
            setImagePreviews((prev) => {
                const updatedImagePreviews = [...prev];
                updatedImagePreviews.push(URL.createObjectURL(file));
                return updatedImagePreviews;
            }
            );
            setInputArray((prev) => {
                const updatedInputArray = [...prev];
                const existingIndex = updatedInputArray.findIndex(
                    (input) => input.input_name === input_name
                );
                if (existingIndex === -1) {
                    updatedInputArray.push({
                        input_name,
                        input_value: uploadedFiles
                    });
                } else {
                    updatedInputArray[existingIndex] = {
                        input_name,
                        input_value: uploadedFiles
                    };
                }
            });
        };

        return (<div className="col-span-full" key={input_name}>
            <label htmlFor={input_name} className="text-subtitle3">
                {description_for_user}
            </label>
            {// a list of an image area per existing image in the input array + a button to load image
                jsonInput.value!.map((image: string, index: number) => {
                    return <ImagePreview sessionId={sessionId} filename={image} alt={jsonInput.description_for_user} />
                })
            }
            {
                imagePreviews.map((image, index) => {
                    <img src={image} alt="Preview" style={{ maxWidth: '300px' }} className="rounded-lg w-full" />
                })
            }
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={newImage}
                className="hidden"
            />
            <Button
                variant="secondary"
                className="min-w-[83px]"
                onClick={() => fileInputRef.current?.click()}
            >
                {t("userTaskExecution.inputsTab.imageUploadButton")}
            </Button>
        
        </div>)
    }
};

export default MultipleImagesArea;