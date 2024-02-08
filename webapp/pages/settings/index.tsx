import Layout from "components/Layout";
import Settings from "modules/Settings";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const SettingsPage = () => {
  return (
    <Layout>
      <Settings />
    </Layout>
  );
};

export default SettingsPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
