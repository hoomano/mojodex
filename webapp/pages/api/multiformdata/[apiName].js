import axios from "axios";
import busboy from "busboy";
import { IncomingForm } from "formidable";
import { createReadStream } from "fs";

export const config = {
    api: {
        bodyParser: false,
    },
};

export default async function handler(req, res) {

    const { apiName } = req.query;


    let headers = {
        "Content-type": req.headers["content-type"] || "application/json",
        Authorization: req.headers.token,
    };

    let requestData = await parseFormDataFormidable(req);


    if (req.method === "POST") {


        try {
            const response = await axios.post(
                `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
                requestData,
                { headers: headers }
            );

            if (response.status !== 200) {
                console.log("🔴 response.status", response.status);
                if (response.data.error) {
                    res.status(response.status).json({ ...response.data, });
                } else {
                    res.status(response.status).json({ error: response.data });
                }
                return;
            }
            return res.status(200).json({
                ...response.data,
            });
        } catch (error) {
            console.log("🔴 Error: ", error);
            return res.status(400).json({ "error": error });
        }
    }

    if (req.method === "PUT") {

        try {
            const response = await axios.put(
                `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
                requestData,
                { headers: headers }
            );

            if (response.status !== 200) {
                if (response.data.error) {
                    res.status(response.status).json({ ...response.data, });
                } else {
                    res.status(response.status).json({ error: response.data });
                }
                return;
            }
            return res.status(200).json({
                ...response.data,
            });
        } catch (error) {
            return res.status(400).json({ ...error.response.data });
        }
    }


}



function parseFormDataFormidable(req) {
    return new Promise((resolve, reject) => {
        const form = new IncomingForm();

        form.parse(req, async function (err, fields, files) {
            if (err) {
                reject(err);
            }

            const formData = {};
            for (const field in fields) {
                formData[field] = fields[field];
            }

            for (const fieldName in files) {
                const fileData = files[fieldName];
                const name = fileData.originalFilename;
                const fileStream = createReadStream(fileData.filepath);
                formData[fieldName] = fileStream;
            }

            resolve(formData);
        });
    });
}
