import React, { Dispatch, SetStateAction, useState, useRef } from 'react';
import { InputArrayProps, TaskJsonInput } from 'modules/Tasks/interface';
import Button from 'components/Button';
import { useTranslation } from "next-i18next";
import { FaFileVideo } from 'react-icons/fa';

interface VideoFileProps {
    jsonInput: TaskJsonInput;
    setInputArray: Dispatch<SetStateAction<InputArrayProps[]>>;
}

const VideoFile = ({ jsonInput, setInputArray }: VideoFileProps) => {
    const { input_name, description_for_user } = jsonInput;
    const [videoFilePreview, setVideoFilePreview] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { t } = useTranslation('dynamic');

    const handleVideoFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;

        if (file && file.type.startsWith('video/')) {
            setVideoFilePreview(file.name);
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
                        accept=".webm,.mp4"
                        onChange={handleVideoFileChange}
                        className="hidden"
                    />
                    <Button
                        variant="secondary"
                        className="min-w-[83px]"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        {videoFilePreview ? ( 
                            <>
                                <div>{videoFilePreview}</div>
                                <FaFileVideo className="w-6 h-6" />
                            </>
                        ) : t("userTaskExecution.inputsTab.videoUploadButton")
                        }
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default VideoFile;