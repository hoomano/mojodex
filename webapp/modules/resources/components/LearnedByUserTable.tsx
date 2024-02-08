import React, { useState } from "react";
import moment from "moment";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRefresh, faTrash } from "@fortawesome/free-solid-svg-icons";
import { Documents } from "../interface";
import Loader from "components/Loader";
import { debounce } from "helpers/method";
import useRefreshDocument from "../hooks/useRefreshDocument";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { ResourceTab } from "..";
import { useTranslation } from "react-i18next";

interface LearnedByUserTableProps {
  onDeleteDocument: (document_pk: number) => void;
  resourceData: Documents[] | undefined;
  isLoading: boolean;
  handleRefetchOnScrollEnd: (e: any) => void;
}

const LearnedByUserTable = ({
  onDeleteDocument,
  resourceData,
  isLoading,
  handleRefetchOnScrollEnd,
}: LearnedByUserTableProps) => {
  const [loadingRow, setLoadingRow] = useState<any>(null);
  const refreshDocument = useRefreshDocument();
  const { showAlert } = useAlert();
  const { t } = useTranslation("dynamic");

  const onRefreshDocument = (document_pk: number) => {
    setLoadingRow(document_pk);
    const payload = {
      datetime: new Date().toISOString(),
      document_pk: document_pk,
    };
    refreshDocument.mutate(payload, {
      onSuccess: () => {
        showAlert({
          title: "Resources Updated",
          type: "success",
        });
        invalidateQuery([cachedAPIName.RESOURCES, ResourceTab.LearnedByUser]);
      },
      onError: (error: any) => {
        showAlert({
          title: error?.error || "something went wrong!",
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
        <table className="w-full">
          <tr className="text-xs text-gray-lighter">
            <th className="font-semibold text-start w-[300px]">
              {t("resources.learnedByUserTableHeader.document")}
            </th>
            <th className="font-semibold text-start">
              {t("resources.learnedByUserTableHeader.addedBy")}
            </th>
            <th className="font-semibold text-start">
              {t("resources.learnedByUserTableHeader.updatedAt")}
            </th>
            <th></th>
          </tr>
          {resourceData?.map((doc, index) => {
            return (
              <tr
                className="border-b border-gray-light text-xs text-gray-dark"
                key={index}
              >
                <td className="py-4 pr-6 break-all font-semibold flex items-center gap-2.5">
                  <img src="/images/resources/link_icon.svg" />
                  {doc.name}
                </td>
                <td className="w-[70px]">{doc.author}</td>
                <td className="w-[80px]">
                  {moment(doc.last_update_date).format("YYYY-MM-DD")}
                </td>
                <td className="text-gray-lighter text-end w-0">
                  <FontAwesomeIcon
                    icon={faRefresh}
                    onClick={() => onRefreshDocument(doc?.document_pk)}
                    className={`cursor-pointer ${
                      doc?.document_pk == loadingRow &&
                      refreshDocument?.isLoading &&
                      "animate-spin"
                    }`}
                  />
                  <FontAwesomeIcon
                    icon={faTrash}
                    className="ml-5 cursor-pointer"
                    onClick={() => onDeleteDocument(doc?.document_pk)}
                  />
                </td>
              </tr>
            );
          })}
        </table>
      )}
    </div>
  );
};

export default LearnedByUserTable;
