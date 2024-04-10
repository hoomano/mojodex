import Button from "components/Button";
import Image from "next/image";
import { useTranslation } from "react-i18next";
import { UserTaskExecution } from "../interface";

interface EmptyStateType {
  startANewTaskHandler: () => void;
  searchInput: string;
  isFollowupsAvailable: boolean;
  userTasksSuggestions: number[];
}

const EmptyState = ({
  startANewTaskHandler,
  searchInput,
  isFollowupsAvailable,
  userTasksSuggestions,
}: EmptyStateType) => {
  const { t } = useTranslation("dynamic");

  const noTasksFound =
    (!!searchInput.length || !isFollowupsAvailable) &&
    (!!userTasksSuggestions.length || !!searchInput.length);

  return (
    <div className="border border-gray-light rounded-lg flex items-center justify-center h-[640px]">
      <div className="text-center">
        {noTasksFound ? (
          <div className="text-h4 mt-2">No tasks found</div>
        ) : (
          <>
            <Image
              src={`/images/task/empty_state.svg`}
              width={34}
              height={34}
              alt="empty"
              className="mx-auto"
            ></Image>
            <div className="text-h4 mt-2">
              {t("startNewTask.noTasksStarted")}
            </div>
            <div className="text-subtitle3 text-gray-lighter my-2">
              {t("startNewTask.getStartedMessage")}
            </div>
            <Button onClick={startANewTaskHandler}>
              {t("startNewTask.startNewTaskButton")}
            </Button>
          </>
        )}
      </div>
    </div>
  );
};

export default EmptyState;
