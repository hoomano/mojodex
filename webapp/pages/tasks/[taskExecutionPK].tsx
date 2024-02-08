import React, { useContext } from "react";
import Layout from "components/Layout";
import DraftDetail from "modules/Tasks/components/TaskExecutionDetail";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { ChatProvider } from "modules/Chat/helpers/ChatContext";
import { ChatUsedFrom } from "modules/Chat/interface/context";
import { useRouter } from "next/router";
import { decryptId } from "helpers/method";
import useGetExecuteTaskById from "modules/Tasks/hooks/useGetExecuteTaskById";
import MobileView from "modules/Tasks/components/MobileView";
import Loader from "components/Loader";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";
import { GetStaticPaths } from "next";

const TaskDetailsPage = () => {
  const router = useRouter();

  const {
    globalState: { newlyCreatedTaskInfo },
  } = useContext(globalContext) as GlobalContextType;

  const taskId = router.query?.taskId
    ? decryptId(router.query.taskId as string)
    : null;

  const taskExecutionPK = router.query?.taskExecutionPK
    ? decryptId(router.query.taskExecutionPK as string)
    : null;

  const { data: currentTaskInfo } = useGetExecuteTaskById(taskExecutionPK, {
    enabled: !taskId && !!taskExecutionPK,
  });

  const taskSessionId =
    currentTaskInfo?.session_id || newlyCreatedTaskInfo?.sessionId;

  return (
    <Layout>
      {taskSessionId ? (
        <ChatProvider
          sessionId={taskSessionId}
          chatUsedFrom={ChatUsedFrom.Task}
        >
          <div className="sm:hidden">
            <MobileView />
          </div>
          <div className="invisible sm:visible">
            <DraftDetail />
          </div>
        </ChatProvider>
      ) : (
        <Loader />
      )}
    </Layout>
  );
};

export default TaskDetailsPage;

export const getStaticPaths: GetStaticPaths<{ slug: string }> = async () => {

  return {
      paths: [], //indicates that no page needs be created at build time
      fallback: 'blocking' //indicates the type of fallback
  }
}

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
