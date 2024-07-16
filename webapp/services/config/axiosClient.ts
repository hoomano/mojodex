import axios from "axios";
import { appVersion, appPlatform } from "helpers/constants/index";
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

  request.headers.version = appVersion;
  request.headers.platform = appPlatform;
 

  if (request.method === "get" || request.method === "delete") {
    console.log("🟢", process.env.NEXT_PUBLIC_VERSION_NUMBER);
    request.params = {
      ...request.params,
      datetime: new Date().toISOString(),
      version: appVersion,
      platform: appPlatform
    };
  } else if(!(request.data instanceof FormData)) {
    request.data = {
      ...request.data,
      datetime: new Date().toISOString(),
      version: appVersion,
      platform: appPlatform
    };
  } else {
    request.data.append("datetime", new Date().toISOString());
    request.data.append("version", appVersion);
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
