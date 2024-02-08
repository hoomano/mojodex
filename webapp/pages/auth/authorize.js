import React from 'react';
import { useSession} from 'next-auth/react';
import { useRouter } from 'next/router'
import {useEffect} from "react";
import { SessionType } from "helpers/interface/session";
import { getToken } from "next-auth/jwt"

const parseAuthorizationData = (response) => {
    let parameter = '?' + new URLSearchParams(response).toString();
    parameter = parameter.replace(/%2F/g, "/");
    parameter = parameter.replace(/%3A/g, ":");
    parameter = parameter.replace(/%3F/g, "?");
    parameter = parameter.replace(/%3D/g, "=");
    parameter = parameter.replace(/%26/g, "&");
    parameter = parameter.replace(/\+/g, " ");
    parameter = parameter.replace(/%2C/g, ",");
    parameter = parameter.replace(/%3B/g, ";");
    parameter = parameter.replace(/%40/g, "@");
    parameter = parameter.replace(/%23/g, "#");
    parameter = parameter.replace(/%24/g, "$");
    parameter = parameter.replace(/%25/g, "%");
    parameter = parameter.replace(/%5E/g, "^");
    parameter = parameter.replace(/%2B/g, "+");
    parameter = parameter.replace(/%3C/g, "<");
    parameter = parameter.replace(/%3E/g, ">");
    parameter = parameter.replace(/%7E/g, "~");
    return parameter
}

const authorize = (props) => {
    const {data: session} = useSession({ required: true });
    const router = useRouter();
    useEffect(() => {
        let next_token = {next_token: props.nextToken};
        if (!session || !router.query.redirect_uri) return ;
        let authorizeData = {...session.user, ...session.authorization, ...next_token};
        let url = router.query.redirect_uri + parseAuthorizationData(authorizeData)
        window.location.href = url;
    }, [session]);
    return (<div></div>)
};

export default authorize;


export async function getServerSideProps({ req }) {
    const rawToken = await getToken({ req, secret: process.env.NEXT_AUTH_JWT_SECRET, raw: 'true' });
    return {
      props: { nextToken: rawToken },
    };
  }
  