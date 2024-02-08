import Layout from "components/Layout";
import Resources from "modules/resources";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const ResourcesPage = () => {
  return (
    <Layout>
      <Resources />
    </Layout>
  );
};

export default ResourcesPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
