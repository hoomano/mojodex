import Layout from "components/Layout";
import { ChatProvider } from "modules/Chat/helpers/ChatContext";
import Chat from "modules/Chat";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faClose } from "@fortawesome/free-solid-svg-icons";
import { useRouter } from "next/router";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const Page = () => {
  const router = useRouter();
  const sessionId = (router.query?.sessionId as string) || null;

  return (
    <Layout>
      <div className={`w-full grow ml-0 justify-center items-center`}>
        <button
          onClick={() => router.push("/drafts")}
          className="absolute top-4 right-4"
        >
          <FontAwesomeIcon
            icon={faClose}
            className="text-gray-400 h-5 hover:text-gray-100 hover:cursor-pointer hover:scale-125 transform transition"
          />
        </button>
        <ChatProvider sessionId={sessionId}>
          <Chat />
        </ChatProvider>
      </div>
    </Layout>
  );
};

export default Page;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
