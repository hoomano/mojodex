import axios from "axios";
import { appPlatform } from "helpers/constants/index";
import { SessionType } from "helpers/interface/session";
import { getSession } from "next-auth/react";

const axiosClient = axios.create({ baseURL: "/" });

let token = "";

axiosClient.interceptors.request.use(async (request) => {
  if (!token.length) {
    const session = (await getSession()) as SessionType | null;
    token = session?.authorization?.token || "";
  }

  request.headers.token = token;

  request.headers.version = process.env.NEXT_PUBLIC_APP_VERSION;
  request.headers.platform = appPlatform;
 

  if (request.method === "get" || request.method === "delete") {
    request.params = {
      ...request.params,
      datetime: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_APP_VERSION,
      platform: appPlatform
    };
  } else if(!(request.data instanceof FormData)) {
    request.data = {
      ...request.data,
      datetime: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_APP_VERSION,
      platform: appPlatform
    };
  } else {
    request.data.append("datetime", new Date().toISOString());
    request.data.append("version", process.env.NEXT_PUBLIC_APP_VERSION!);
    request.data.append("platform", appPlatform);
  }

  return request;
});

axiosClient.interceptors.response.use(
  (response) => {
    // Response with 2xx status code lies here
    return response.data;
  },
  (error) => {
    // Error handling goes here...
    return Promise.reject(error.response.data);
  }
);

export default axiosClient;
