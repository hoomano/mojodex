import Layout from "components/Layout";
import DeleteAccount from "modules/DeleteAccount";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const DeleteAccountPage = () => {
  return (
    <Layout>
      <DeleteAccount />
    </Layout>
  );
};

export default DeleteAccountPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
