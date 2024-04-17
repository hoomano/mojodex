import Layout from "components/Layout";
import Role from "modules/Role";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const RolePage = () => {
  return (
    <Layout>
      <Role />
    </Layout>
  );
};

export default RolePage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
