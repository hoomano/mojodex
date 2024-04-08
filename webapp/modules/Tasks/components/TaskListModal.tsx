import { useContext, useMemo } from "react";
import Modal from "components/Modal";
import { UserTask } from "../interface";
import TaskCard from "./TaskCard";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useRouter } from "next/router";
import { encryptId } from "helpers/method";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { useTranslation } from "react-i18next";

interface TaskListModalType {
  tasks: UserTask[] | undefined;
  isOpen: boolean;
  closed: () => void;
}

const TaskListModal = ({ tasks = [], isOpen, closed }: TaskListModalType) => {
  const router = useRouter();
  const { globalState } = useContext(globalContext) as GlobalContextType;
  const { t } = useTranslation("dynamic");

  const hasPurchasePlan = !!tasks.find((task) => task.enabled);
  
  return (
    <div>
      <Modal
        isOpen={isOpen}
        footerPresent={false}
        headerPresent={false}
        widthClass="max-w-[880px]"
      >
        <div className="p-[60px]">
          <XMarkIcon
            className="h-6 w-6 text-gray-lighter absolute right-6 top-6 cursor-pointer"
            aria-hidden="true"
            onClick={closed}
          />

          <div className="relative">
            {!hasPurchasePlan && (
              <div className="w-full h-full absolute flex justify-center z-20 backdrop-blur-[3px]">
                <button
                  className="z-10 bg-blue-700 text-white p-4 rounded-lg h-max mt-52"
                  onClick={() => router.push("/purchase")}
                >
                  🌟 Upgrade now
                </button>
              </div>
            )}

            <div className="text-h3">{t("newUserTaskExecution.title")}</div>

            <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
              {t("newUserTaskExecution.selectBusinessTasks")}
            </div>
            <div className="sm:grid sm:grid-cols-3 sm:gap-[20px] mt-2">
              {tasks.map(
                ({
                  user_task_pk,
                  task_name,
                  task_description,
                  task_icon,
                  enabled,
                  task_type
                }) => (
                  <TaskCard
                    key={user_task_pk}
                    title={task_name}
                    description={task_description}
                    icon={task_icon}
                    onClick={() =>
                      router.push(`/tasks/create/${encryptId(user_task_pk)}`)
                    }
                    enabled={enabled}
                    task_type={task_type}
                  />
                )
              )}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default TaskListModal;
