import { getToken } from "next-auth/jwt"
import {AxiosError} from 'axios';


export async function checkParams(res: any, params: {}, requiredParams: []) {
    let missingParams : [] = [];
    for (const param of requiredParams) {
        if (params[param] === undefined) {
            missingParams.push(param);
        }
    }
    if (missingParams.length != 0) {
        res.status(400).json({ "error": 'missing parameters', "params" : missingParams});
        return false;
    }
    return true;
}

export async function authenticate(req : any, res : any) {
    const token = await getToken({ req, secret: process.env.NEXT_AUTH_JWT_SECRET });
    if (!token) {
        res.status(401).json({ "error": "not connected" });
        return false;
    }
    return true;
}

export async function callApi(req : any, res: any, api : Function, onsuccess? : Function, onerror? : Function) {
    let response;
    
    try {
        response = await api(req, res);
    } catch (e) {
        if (e instanceof AxiosError && onerror === undefined) {
            console.error('🔴 Error in:', api.name, 'method:', req.method, 'error:', e.response?.data);
            res.status(400).json({...e.response?.data});
            return;
        }
        if (e === undefined || onerror === undefined) {
            console.error('🔴 Error in:', api.name, 'method:', req.method, 'error:', e);
            res.status(400).json({"error": e, "method": req.method});
            return;
        }
        await onerror(req, response);
        return;
    }
    if (onsuccess !== undefined) {
        await onsuccess(req, response);
        return ;
    }
    if (response === undefined || response === null) {
        if (!res.headersSent) {
            res.status(500).json({"error": 'response is undefined or null', "method": req.method});
        }
        return;
    }
    if (response.status === undefined || response.data === undefined) {
        console.error('🔴 Error in:', api.toString(), 'method:', req.method, 'error:', 'response.status or response.data is undefined');
        res.status(500).json({"error": 'response.status or response.data is undefined', "method": req.method});
        return;
    }
    res.setHeader('Content-Type', 'application/json');
    console.log('🟢 Success ',req.method, ": ", req.url);
    res.status(response.status).json(response.data);
}

export async function callApiWithAuth(req : any, res: any, api : Function, onsuccess? : Function, onerror? : Function) {
    if (!await authenticate(req, res)) return;
    await callApi(req, res, api, onsuccess, onerror);
}

export async function requestHandler(req: any, res: any, handlers: any, api: any) {
    if (!handlers[req.method] === undefined) {
        res.status(405).json({ "error": 'method not allowed' });
        return;
    }
    if (api[req.method] === undefined) {
        res.status(500).json({ "error": 'no api provide' });
        return;
    }
    await handlers[req.method](req, res, api[req.method]);
}