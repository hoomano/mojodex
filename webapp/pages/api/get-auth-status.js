import axios from "axios";
import { getToken } from "next-auth/jwt";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");

  const token = await getToken({ req, secret: process.env.NEXT_AUTH_JWT_SECRET });

  res.setHeader("Content-Type", "application/json");
  return res.status(200).json({ token });
}
