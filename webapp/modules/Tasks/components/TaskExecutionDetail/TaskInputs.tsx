import { TaskJsonInput } from "modules/Tasks/interface";
import React, { FunctionComponent, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
interface TaskInputsProps {
    inputs: TaskJsonInput[];
    sessionId: string;
}

interface ImageWithHeadersProps {
    sessionId: string;
    filename: string;
    alt: string;
}

const ImageWithHeaders: FunctionComponent<ImageWithHeadersProps> = ({ sessionId, filename, alt }) => {
    const [imgSrc, setImgSrc] = useState("");
    const { update: updateAuthSession, data: session }: any = useSession();


    useEffect(() => {
        fetch(`/api/image?datetime=${new Date().getTime()}&session_id=${sessionId}&filename=${filename}`, {
            headers: {
                'token': session.authorization.token
            },
        })
            .then(response => response.blob())
            .then(images => {
                let objectURL = URL.createObjectURL(images);
                setImgSrc(objectURL);
            });
    }, [sessionId, filename]);

    return (
        <img src={imgSrc} alt={alt} style={{ height: 300, objectFit: "contain" }} />
    );
};

const TaskInputs: FunctionComponent<TaskInputsProps> = ({ inputs, sessionId }) => {
    return (
        <div className="p-[30px] w-full">
            <ul role="list" className="space-y-6 w-full">
                {inputs?.map((input, index) => (
                    <li key={index} className="relative flex flex-col">
                        <h1 className="text-xl font-bold mb-2">{input.description_for_user}</h1>
                        
                        {input.type === "image" ? (
                            <>
                            <p>{input.value}</p>
                            <ImageWithHeaders sessionId={sessionId} filename={input.value!} alt={input.description_for_user} />
                            </>
                        ) : (
                            <>
                                
                                <p className="text-sm text-justify">
                                    {input.value?.split('\n').map((line, index) => (
                                        <React.Fragment key={index}>
                                            {line}
                                            <br />
                                        </React.Fragment>
                                    ))}
                                </p>
                            </>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default TaskInputs;