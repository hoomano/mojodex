import React, { Dispatch, SetStateAction, useState, useRef, useEffect } from 'react';
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
            setUploadedFiles((prev) => {
                const updatedUploadedFiles = [...prev];
                updatedUploadedFiles.push(file);
                return updatedUploadedFiles;
            });
            setInputArray((prev) => {
                const updatedInputArray = [...prev];
                let n = jsonInput.value?.length ?? 0 + imagePreviews.length;
                let input_name_i = input_name + "_" + n;
               
                updatedInputArray.push({
                    input_name: input_name_i,
                    input_value: file
                });
               
                return updatedInputArray;
            });
        }
    };

        return (<div className="col-span-full" key={input_name}>
            <label htmlFor={input_name} className="text-subtitle3">
                {description_for_user}
            </label>
            <div>
            {// a list of an image area per existing image in the input array + a button to load image
                jsonInput.value != null && jsonInput.value!.map((image: string, index: number) => {
                    return <ImagePreview sessionId={sessionId} filename={image} alt={jsonInput.description_for_user} />
                })
                }
                </div>
            <div>
            {
                imagePreviews.map((image, index) => {
                    return <img src={image} alt="Preview" style={{ maxWidth: '300px' }} className="rounded-lg w-full" />
                })
                }
            </div>
            <div>
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
                </Button></div>
            
        
        </div>)
    
};

export default MultipleImagesArea;