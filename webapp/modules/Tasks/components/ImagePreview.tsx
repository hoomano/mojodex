import { useSession } from "next-auth/react";
import { FunctionComponent, useState, useEffect } from "react";

interface ImageWithHeadersProps {
    sessionId: string;
    filename: string;
    alt: string;
}

const ImagePreview: FunctionComponent<ImageWithHeadersProps> = ({ sessionId, filename, alt }) => {
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

export default ImagePreview;