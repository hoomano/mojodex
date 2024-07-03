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
import TaskProvider from "modules/Tasks/helpers/TaskContext";

const TaskDetailsPage = () => {
  const router = useRouter();


  const taskExecutionPK = router.query?.taskExecutionPK
    ? decryptId(router.query.taskExecutionPK as string)
    : null;

  
  const { data: currentTaskInfo } = useGetExecuteTaskById(taskExecutionPK);
  
  const taskSessionId = currentTaskInfo?.session_id;
 
  return (
    <Layout>
      {taskSessionId ? (
        <ChatProvider
          sessionId={taskSessionId}
          currentTaskInfo={{
            producedTextPk: currentTaskInfo!.produced_text_pk,
            taskExecutionPK: currentTaskInfo!.user_task_execution_pk
          }}
          chatUsedFrom={currentTaskInfo?.task_type === "workflow" ? ChatUsedFrom.Workflow : ChatUsedFrom.Task}
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
