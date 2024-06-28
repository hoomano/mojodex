// A React component that add renders an edit button that will switch between a text + edit butto into an Input with save button that calls a backend route on save

import React, { useState } from "react";
import { FaEdit, FaSave } from "react-icons/fa";
// import { useTranslation } from "next-i18next";

import TextareaAutosize from 'react-textarea-autosize';

interface EditableTextProps {
    text: string;
    onSave: (title: string) => void;
}

export const EditableText: React.FC<EditableTextProps> = ({ text, onSave }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [title, setTitle] = useState(text);
    // const { t } = useTranslation('dynamic');

    const handleSave = () => {
        onSave(title);
        setIsEditing(false);
    }

    return (
        <div className="flex flex-row items-center">
            {isEditing ? (
                <>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="border border-2 border-primary-main grow py-0.5 text-h4 font-semibold leading-5 text-gray-darker resize-none w-full"

                    />
                    {/* <TextareaAutosize 
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="border-none grow py-0.5 text-h4 font-semibold leading-5 text-gray-darker resize-none w-full"

                    /> */}
                    <button onClick={handleSave} className="ml-2">
                        <FaSave className="text-gray-dark flex-none" />
                    </button>
                </>
            ) : (
                <>

                    <div className="text-h4 font-semibold text-gray-darker">
                      {title}
                    </div>
                    <button onClick={() => setIsEditing(true)} className="ml-2">
                        <FaEdit className="text-gray-dark flex-none" />
                    </button>
                </>
            )}
        </div>
    );
};