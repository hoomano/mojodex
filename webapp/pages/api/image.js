import axios from "axios";

export default async function handler(req, res) {
    const  apiName  = 'image';

    let headers = {
        "Content-type": req.headers["content-type"] || "application/json",
        Authorization: req.headers.token,
    };

    if (req.method === "GET") {
        try {
            const response = await axios.get(
                `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
                { headers, params: req.query, responseType: 'stream' }
            );
            // Set headers from Python backend response
            Object.keys(response.headers).forEach(key => {
                res.setHeader(key, response.headers[key]);
            });

            // Stream the response from Python backend to client
            response.data.pipe(res);
        } catch (error) {
            console.log("🔴 ", error);
            return res.status(400).json({ "error": error});
        }
    }



}