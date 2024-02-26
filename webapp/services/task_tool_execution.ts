import { apiRoutes } from "services";
import axiosClient from "./config/axiosClient";
import { approveTaskToolExecutionPayload } from "modules/TaskToolExecution/interface";



export const approveTaskToolExecution = (payload: approveTaskToolExecutionPayload) =>
    axiosClient.post(apiRoutes.acceptTaskToolExecution, payload);

