import axios from "axios";

export default async function handler(req, res) {
    const  apiName  = "is_email_service_configured";
    console.log("👉 ", process.env.MOJODEX_WEBAPP_SECRET);
    let headers = {
        "Content-type": req.headers["content-type"] || "application/json",
        // This is the secret key for the webapp to access the backend. User is not logged in, and we don't need a token here.
        Authorization: process.env.MOJODEX_WEBAPP_SECRET,
    };

    if (req.method === "GET") {
        try {
            const response = await axios.get(
                `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
                { headers, params: req.query }
            );
            if (response.status !== 200) {
                if (response.data.error) {
                    res.status(response.status).json({ ...response.data, });
                } else {
                    res.status(response.status).json({ error: response.data });
                }
                return;
            }
            return res.status(200).json({ ...response.data });
        } catch (error) {
            return res.status(400).json({ ...error.response.data });
        }
    }

}