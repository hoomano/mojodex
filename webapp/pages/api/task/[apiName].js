import axios from "axios";
import { getToken } from "next-auth/jwt";
import fs from "fs";
import formidable from "formidable";
const request = require("request");

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");

  const { apiName } = req.query;

  const token = await getToken({ req, secret: process.env.NEXT_AUTH_JWT_SECRET });

  if (!token) {
    res.status(401).json({ session_id: "not connected" });
    return;
  }

  let headers = {
    "Content-type": "application/json; charset=UTF-8",
    Authorization: req.headers.token,
  };

  if (req.method === "GET") {
    try {
      const response = await axios.get(
        `${process.env.MOJODEX_BACKEND_URI}/${apiName}`,
        { headers: headers, params: req.query }
      );

      if (response.status !== 200) {
        console.error("🔴 Tasks:", error);
        res.status(400).json({ error: error });
        return;
      }
      res.setHeader("Content-Type", "application/json");
      res.status(200).json({
        ...response.data,
      });
    } catch (error) {
      console.error("🔴 Tasks :", error);
      res.status(400).json({ error: error });
    }
  }

  if (req.method === "POST") {
    let reqRead = req.read();
    let body = {};
    if (reqRead !== null) {
      console.log(reqRead);
      let stringBody = Buffer.from(reqRead).toString();

      console.log(stringBody);
      body = JSON.parse(stringBody);
    }
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
      res.status(400).json({ error: error });
    }
  }

  if (req.method === "PUT") {
    if (apiName == "user_followup") {
      await userFollowup(req, res);
      return;
    }
    let reqRead = req.read();
    let body = {};
    if (reqRead !== null) {
      console.log(reqRead);
      let stringBody = Buffer.from(reqRead).toString();

      console.log(stringBody);
      body = JSON.parse(stringBody);
    }
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
      res.status(400).json({ error: error });
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
      res.status(200).json({ ...response.data });
    } catch (error) {
      res.status(400).json({ error: error });
    }
  }
}
