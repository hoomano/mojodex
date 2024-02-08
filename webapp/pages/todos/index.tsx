import Layout from "components/Layout";
import TodosDrawer from "modules/TodosDrawer";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const TodosPage = () => {
  return (
    <Layout>
      <TodosDrawer />
    </Layout>
  );
};

export default TodosPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
