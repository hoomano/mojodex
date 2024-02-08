import React, { useContext, useState } from "react";
import Button from "components/Button";
import Tab from "components/Tab";
import AddedByMossTable from "./components/LearnedByUserTable";
import useGetResources from "./hooks/useGetResources";
import LearnedByMojoTable from "./components/LearnedByMojoTable";
import useDeleteResource from "./hooks/useDeleteResource";
import AddDocumentModal from "./components/AddDocumentModal";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import useAlert from "helpers/hooks/useAlert";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

export enum ResourceTab {
  LearnedByUser = "learnedByUser",
  LearnedByMojo = "learnedByMojo",
}

const Resources = () => {
  const [selectedTab, setSelectedTab] = useState<ResourceTab>(
    ResourceTab.LearnedByUser
  );
  const [addDocumentModal, setAddDocumentModal] = useState(false);
  const deleteDocument = useDeleteResource();
  const { showAlert } = useAlert();
  const router = useRouter();
  const { t } = useTranslation("dynamic");

  const {
    fetchNextPage,
    data: resourceDetail,
    isLoading: isDocumentsLoading,
    isFetching,
  } = useGetResources(selectedTab);

  const {
    globalState: { session },
  } = useContext(globalContext) as GlobalContextType;

  const onDeleteDocument = (document_pk: number) => {
    deleteDocument.mutate(document_pk, {
      onSuccess: () => {
        showAlert({
          title: "Document deleted successfully.",
          type: "success",
        });
        invalidateQuery([cachedAPIName.RESOURCES]);
      },
      onError: () => {
        showAlert({
          title: "Something went wrong!",
          type: "error",
        });
      },
    });
  };

  const resourceList =
    resourceDetail?.pages?.flatMap((data) => data.documents) || [];

  const handleRefetchOnScrollEnd = async (e: any) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (!isFetching && scrollHeight - scrollTop <= clientHeight * 1.2) {
      await fetchNextPage({ pageParam: resourceList.length });
    }
  };

  const userName = (
    session?.user?.name ||
    session?.authorization?.name ||
    "User"
  )?.split(" ")?.[0];

  const tabs = [
    {
      key: ResourceTab.LearnedByUser,
      title: `${t("resources.addedByUserTabTitle")} ${userName}`,
      component: (
        <AddedByMossTable
          onDeleteDocument={onDeleteDocument}
          resourceData={resourceList}
          isLoading={isDocumentsLoading}
          handleRefetchOnScrollEnd={handleRefetchOnScrollEnd}
        />
      ),
    },
    {
      key: ResourceTab.LearnedByMojo,
      title: `${t("resources.learnedByMojoTabTitle")}`,
      component: (
        <LearnedByMojoTable
          onDeleteDocument={onDeleteDocument}
          resourceData={resourceList}
          isLoading={isDocumentsLoading}
          handleRefetchOnScrollEnd={handleRefetchOnScrollEnd}
        />
      ),
    },
  ];

  return (
    <div className="px-[90px] pt-10">
      <div className="flex items-center justify-between pb-[25px]">
        <div className="flex items-center gap-5">
          <button onClick={router.back}>
            <img alt="back" src="/images/resources/left_arrow.svg" />
          </button>
          <div className="text-h2 font-semibold">
            {t("resources.resourcesTitle")}
          </div>
        </div>
        <Button
          className="bg-gray-light"
          variant={"outline"}
          onClick={() => setAddDocumentModal(true)}
        >
          {t("resources.addButton")}
        </Button>
      </div>
      <Tab
        selected={selectedTab}
        onChangeTab={(key) => setSelectedTab(key as ResourceTab)}
        tabs={tabs}
      />
      <AddDocumentModal
        isOpen={addDocumentModal}
        closed={() => setAddDocumentModal(false)}
      />
    </div>
  );
};

export default Resources;
