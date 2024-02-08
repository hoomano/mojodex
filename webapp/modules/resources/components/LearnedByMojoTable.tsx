import React, { Fragment, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faClose,
  faPencil,
  faTrash,
  faChevronDown,
  faChevronRight,
} from "@fortawesome/free-solid-svg-icons";
import moment from "moment";
import { Documents } from "../interface";
import Loader from "components/Loader";
import { debounce } from "helpers/method";
import useRefreshDocument from "../hooks/useRefreshDocument";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { ResourceTab } from "..";
import { useTranslation } from "react-i18next";

interface LearnedByMojoTableProps {
  onDeleteDocument: (document_pk: number) => void;
  resourceData: Documents[] | undefined;
  isLoading: boolean;
  handleRefetchOnScrollEnd: (e: any) => void;
}

const LearnedByMojoTable = ({
  onDeleteDocument,
  resourceData,
  isLoading,
  handleRefetchOnScrollEnd,
}: LearnedByMojoTableProps) => {
  const [accordion, setAccordion] = useState<null | number>(null);
  const [editText, setEditText] = useState<any>(null);
  const refreshDocument = useRefreshDocument();
  const { showAlert } = useAlert();
  const { t } = useTranslation("dynamic");

  const onAccordionHandler = (id: number) => {
    setAccordion((prevId) => (prevId === id ? null : id));
  };

  const onDocumentNameUpdate = (document_pk: number) => {
    const payload = {
      datetime: new Date().toISOString(),
      document_pk: document_pk,
      edition: editText?.text || "",
    };

    refreshDocument.mutate(payload, {
      onSuccess: () => {
        showAlert({
          title: "Text updated successfully.",
          type: "success",
        });
        setEditText(null);
        invalidateQuery([cachedAPIName.RESOURCES, ResourceTab.LearnedByMojo]);
      },
      onError: (error: any) => {
        showAlert({
          title: error?.error,
          type: "error",
        });
      },
    });
  };

  return (
    <div
      className="px-3 mt-5 h-[430px] overflow-auto mb-5"
      onScroll={debounce(handleRefetchOnScrollEnd)}
    >
      {isLoading ? (
        <Loader />
      ) : (
        <>
          <div className="flex items-center text-xs text-gray-lighter">
            <div className="w-[50%] font-semibold">
              {t("resources.learnedByMojoTableHeader.document")}
            </div>
            <div className="w-[20%] font-semibold">
              {t("resources.learnedByMojoTableHeader.conversationWith")}
            </div>
            <div className="w-[20%] font-semibold">
              {t("resources.learnedByMojoTableHeader.updatedAt")}
            </div>
            <div className="w-[10%]"></div>
          </div>
          {resourceData?.map((doc, index) => {
            return (
              <Fragment key={index}>
                <div
                  className={`${
                    doc.document_pk !== accordion &&
                    "border-b border-gray-light"
                  } flex items-center text-xs text-gray-dark`}
                >
                  <div className="w-[50%] py-4 pr-8 break-all font-semibold flex items-center gap-2.5">
                    <img src="/images/resources/chat_icon.svg" />
                    <div>{doc.name}</div>
                  </div>
                  <div className="w-[20%]">{doc.author}</div>
                  <div className="w-[20%]">
                    {moment(doc.last_update_date).format("YYYY-MM-DD")}
                  </div>
                  <div
                    onClick={() => onAccordionHandler(doc?.document_pk)}
                    className="w-[10%]"
                  >
                    <FontAwesomeIcon
                      icon={
                        doc.document_pk === accordion
                          ? faChevronDown
                          : faChevronRight
                      }
                      className="text-gray-lighter cursor-pointer"
                    />
                  </div>
                </div>
                {doc.document_pk === accordion && (
                  <div
                    className={`${
                      accordion && "border-b border-gray-light pb-4"
                    }`}
                  >
                    {doc.document_pk === editText?.document_pk ? (
                      <textarea
                        id="text"
                        name="text"
                        value={editText?.text || ""}
                        onChange={(e) =>
                          setEditText({
                            document_pk: editText?.document_pk,
                            text: e.target.value,
                          })
                        }
                        autoFocus
                        className="w-full bg-transparent border-0 text-xs p-0"
                      />
                    ) : (
                      <div className="text-xs text-gray-dark pb-2">
                        {doc?.text}
                      </div>
                    )}
                    {doc.document_pk === editText?.document_pk ? (
                      <>
                        <FontAwesomeIcon
                          icon={faCheck}
                          className="text-gray-lighter text-xs cursor-pointer"
                          onClick={() =>
                            onDocumentNameUpdate(editText?.document_pk)
                          }
                        />
                        <FontAwesomeIcon
                          icon={faClose}
                          className="ml-2 text-gray-lighter text-xs cursor-pointer"
                          onClick={() => setEditText(null)}
                        />
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon
                          icon={faPencil}
                          className="text-gray-lighter text-xs cursor-pointer"
                          onClick={() => setEditText(doc)}
                        />
                        {doc?.document_pk !== "user_description" &&
                          doc?.document_pk !== "company_description" && (
                            <FontAwesomeIcon
                              icon={faTrash}
                              className="ml-5 text-gray-lighter text-xs cursor-pointer"
                              onClick={() => {
                                console.log("doc?.document_pk", doc);
                                onDeleteDocument(doc?.document_pk);
                              }}
                            />
                          )}
                      </>
                    )}
                  </div>
                )}
              </Fragment>
            );
          })}
        </>
      )}
    </div>
  );
};

export default LearnedByMojoTable;
