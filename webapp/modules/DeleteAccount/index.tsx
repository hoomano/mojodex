import { useSession } from "next-auth/react";
import { useTranslation } from "react-i18next";

const DeleteAccount = () => {
  const { t } = useTranslation("dynamic");

  const session = useSession();

  const handleDeleteRequest = () => {
    // TODO: Implement delete account functionality
    console.log("requestAccountDeletionButton > handleDeleteRequest > not implemented");
  };

  return (
    <div className="flex justify-center h-screen">
      <div className="bg-white py-12 px-6 sm:py-12 lg:px-8">
        <div className="text-2xl font-semibold mb-2 text-center">
          {t("accountDeletion.title")}
        </div>
        <div className="text-sm my-7 bg-[#F5F4FA] p-4 rounded-lg w-[340px] shadow-md">
          {t("accountDeletion.body")}
        </div>
        <button
          className="bg-[#E14546] text-white w-full rounded-lg p-2"
          onClick={handleDeleteRequest}
        >
          {t("accountDeletion.requestAccountDeletionButton")}
        </button>
      </div>
    </div>
  );
};

export default DeleteAccount;
