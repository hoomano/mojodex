import Layout from "components/Layout";
import Purchase from "modules/Purchase";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const PurchasePage = () => {
  return (
    <Layout>
      <Purchase />
    </Layout>
  );
};

export default PurchasePage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
