import Head from "next/head";
import { SessionProvider } from "next-auth/react";
import { GlobalContextProvider } from "helpers/GlobalContext";
import type { AppProps } from "next/app";
import { QueryClientProvider } from "@tanstack/react-query";
import { Hanken_Grotesk } from "next/font/google";
import "../styles/globals.css";
import { appWithTranslation } from "next-i18next";
import queryClient from "./../services/config/queryClient";
import AlertContainer from "components/Alerts/AlertContainer";
import AcceptTermsAndConditionModal from "components/AcceptTermsAndConditionModal";
import { ReactElement, ReactNode } from "react";
import { NextPage } from "next";
import TaskProvider from "modules/Tasks/helpers/TaskContext";
const hanken = Hanken_Grotesk({ subsets: ["latin"] });

export type NextPageWithLayout<P = {}, IP = P> = NextPage<P, IP> & {
  getLayout?: (page: ReactElement) => ReactNode;
};

type AppPropsWithLayout = AppProps & {
  Component: NextPageWithLayout;
};

function MyApp({
  Component,
  pageProps: { session, ...pageProps },
}: AppPropsWithLayout) {
  const getLayout = Component.getLayout ?? ((page) => page);

  return (
    <>
      <GlobalContextProvider>
        <style jsx global>{`
          html {
            font-family: ${hanken.style.fontFamily};
          }
        `}</style>
        <QueryClientProvider client={queryClient}>
          <SessionProvider
            session={session}
            refetchOnWindowFocus={false}
            refetchWhenOffline={false}
          >
            <TaskProvider>
              {getLayout(<Component {...pageProps} />)}
            </TaskProvider>
            <AcceptTermsAndConditionModal />
          </SessionProvider>
        </QueryClientProvider>
        <AlertContainer />
      </GlobalContextProvider>
    </>
  );
}

export default appWithTranslation(MyApp);
