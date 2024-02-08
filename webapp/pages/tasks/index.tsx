import Layout from "components/Layout";
import Tasks from "modules/Tasks";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const Page = () => {
  return (
    <Layout>
      <Tasks />
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
