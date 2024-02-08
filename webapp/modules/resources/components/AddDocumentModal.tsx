import Modal from "components/Modal";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useState } from "react";
import Button from "components/Button";
import useAddDocument from "../hooks/useAddDocument";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { ResourceTab } from "..";

interface AddDocumentModalType {
  isOpen: boolean;
  closed: () => void;
}

const AddDocumentModal = ({ isOpen, closed }: AddDocumentModalType) => {
  const [website, setWebsite] = useState("");
  const addDocument = useAddDocument();
  const { showAlert } = useAlert();

  const onSubmit = (website: string) => {
    addDocument.mutate(website, {
      onSuccess: () => {
        showAlert({
          title: "Document added successfully.",
          type: "success",
        });
        closed();
        setWebsite("");
        invalidateQuery([cachedAPIName.RESOURCES, ResourceTab.LearnedByUser]);
      },
      onError: (error: any) => {
        showAlert({
          title: error?.error || "Something went wrong!",
          type: "error",
        });
      },
    });
  };

  return (
    <div>
      <Modal
        isOpen={isOpen}
        footerPresent={false}
        headerPresent={false}
        widthClass="max-w-[620px]"
      >
        <div className="p-[60px] text-center">
          <XMarkIcon
            className="h-6 w-6 text-gray-lighter absolute right-6 top-6 cursor-pointer"
            aria-hidden="true"
            onClick={closed}
          />
          <div className="text-h4 font-semibold">Add document</div>
          <div className="text-sm text-[#7788A4] mt-2.5">
            Add any website Mojo will analyze it and will use this information
            to answer questions
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              onSubmit(website);
            }}
            className="flex flex-col gap-20 mt-[30px]"
          >
            <input
              type="url"
              name="Website"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="Site web"
              className="block w-full mx-auto rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
              required
            />
            <Button
              className="self-center"
              type="submit"
              isLoading={addDocument?.isLoading}
            >
              Add
            </Button>
          </form>
        </div>
      </Modal>
    </div>
  );
};

export default AddDocumentModal;
