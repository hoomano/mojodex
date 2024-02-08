import axios from "axios";

export default async function handler(req, res) {
  const { apiName } = req.query;

  let headers = {
    "Content-type": "application/json; charset=UTF-8",
  };

  if (req.method === "GET") {
    try {
      const response = await axios.get(
        `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
        { headers: headers, params: req.query }
      );

      res.setHeader("Content-Type", "application/json");
      res.status(200).json({ ...response.data });
    } catch (error) {
      res.status(400).json({ ...error.response.data });
    }
  }

  if (req.method === "POST") {
    const { body } = req;
    try {
      const response = await axios.post(
        `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
        body,
        { headers: headers }
      );

      if (response.status !== 200) {
        res.status(400).json({ error: error });
        return;
      }
      res.setHeader("Content-Type", "application/json");
      res.status(200).json({
        ...response.data,
      });
    } catch (error) {
      res.status(400).json({ ...error.response.data });
    }
  }

  if (req.method === "PUT") {
    const { body } = req;
    try {
      const response = await axios.put(
        `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
        body,
        { headers: headers }
      );

      if (response.status !== 200) {
        res.status(400).json({ error: error });
        return;
      }
      res.setHeader("Content-Type", "application/json");
      res.status(200).json({
        ...response.data,
      });
    } catch (error) {
      res.status(400).json({ ...error.response.data });
    }
  }

  if (req.method === "DELETE") {
    try {
      const response = await axios.delete(
        `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
        { headers: headers, params: req.query }
      );

      if (response.status !== 200) {
        res.status(400).json({ error: error });
        return;
      }
      res.setHeader("Content-Type", "application/json");
      res.status(200).json({
        ...response.data,
      });
    } catch (error) {
      res.status(400).json({ ...error.response.data });
    }
  }
}
