import React, { useState } from "react";
import { FaEdit, FaSave } from "react-icons/fa";

interface EditableTextProps {
    text: string;
    onSave: (title: string) => void;
}

export const EditableText: React.FC<EditableTextProps> = ({ text, onSave }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [title, setTitle] = useState(text);

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
                        className="border-2 border-primary-main grow py-0.5 text-h4 font-semibold leading-5 text-gray-darker resize-none w-full"

                    />
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