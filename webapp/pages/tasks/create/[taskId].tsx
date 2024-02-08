import Layout from "components/Layout";
import CreateTaskForm from "modules/Tasks/components/TaskForm";
import React from "react";
import { GetStaticPaths } from "next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const CreateTask = () => {
  return (
    <Layout>
      <CreateTaskForm />
    </Layout>
  );
};

export default CreateTask;

export const getStaticPaths: GetStaticPaths<{ slug: string }> = async () => {
  return {
    paths: [],
    fallback: "blocking",
  };
};

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
