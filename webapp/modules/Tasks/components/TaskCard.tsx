import React, { useEffect, useState } from "react";
import { UserTaskExecution } from "../interface";
import useDeleteUserTaskExecution from "../hooks/useDeleteUserTaskExecution";
import useAlert from "helpers/hooks/useAlert";
import { invalidateQuery } from "services/config/queryClient";
import cachedAPIName from "helpers/constants/cachedAPIName";
import { EllipsisVerticalIcon } from "@heroicons/react/24/outline";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useTranslation } from "react-i18next";

type Props = {
  title: string;
  description: string;
  showActions?: boolean;
  icon?: string;
  onClick?: () => void;
  enabled?: boolean;
  task?: UserTaskExecution;
  isListView?: boolean;
  task_type: string;
};

const TaskCard = ({
  icon = "✉️",
  title,
  description,
  showActions = false,
  onClick,
  enabled=true,
  task,
  isListView,
  task_type,
}: Props) => {
  let containerClassName =
    "cursor-pointer rounded border p-[20px] border-gray-light group relative bg-white focus-within:ring-2 focus-within:ring-inset focus-within:ring-indigo-500 w-full max-w-[290px]";

  if (!enabled) {
    containerClassName +=
      "cursor-not-allowed pointer-events-none opacity-40 cursor-";
  }

  const [timeAgo, setTimeAgo] = useState("");
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const { showAlert } = useAlert();
  const deleteUserTaskExecution = useDeleteUserTaskExecution();
  const { t } = useTranslation("dynamic");

  useEffect(() => {
    const calculateTimeAgo = () => {
      const currentDate: any = new Date();
      const providedDate: any = task?.start_date
        ? new Date(task.start_date)
        : null;
      const timeDifference = currentDate - providedDate;

      // Calculate minutes, hours, and days
      const minutes = Math.floor(timeDifference / (1000 * 60));
      const hours = Math.floor(timeDifference / (1000 * 60 * 60));
      const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));

      if (minutes < 1) {
        setTimeAgo(t('userTaskExecutionList.date.now'));
      } else if (hours < 1) {
        setTimeAgo(`${t('userTaskExecutionList.date.afterTimeAgo')} ${minutes}${t('userTaskExecutionList.date.minutes')} ${t('userTaskExecutionList.date.afterTimeAgo')}`);
      } else if (days < 1) {
        setTimeAgo(`${t('userTaskExecutionList.date.beforeTimeAgo')}${hours}${t('userTaskExecutionList.date.hours')} ${t('userTaskExecutionList.date.afterTimeAgo')}`);
      } else if (days <= 7) {
        const dayOfWeek = [t('userTaskExecutionList.date.sunday'),
          t('userTaskExecutionList.date.monday'),
          t('userTaskExecutionList.date.tuesday'),
          t('userTaskExecutionList.date.wednesday'),
          t('userTaskExecutionList.date.thursday'),
          t('userTaskExecutionList.date.friday'),
          t('userTaskExecutionList.date.saturday')][
          providedDate?.getDay()
        ];
        const timeString = `${dayOfWeek} ${providedDate?.toLocaleTimeString(
          [],
          {
            hour: "2-digit",
            minute: "2-digit",
          }
        )}`;
        setTimeAgo(`${timeString}`);
      } else {
        setTimeAgo(providedDate?.toISOString().slice(0, 10));
      }
    };

    calculateTimeAgo();
  }, [task?.start_date]);

  const onDeleteUserTaskExecution = (userTaskExecutionPk: any) => {
    deleteUserTaskExecution.mutate(userTaskExecutionPk, {
      onSuccess: () => {
        showAlert({
          title: t('userTaskExecutionList.deleteSuccess'),
          type: "success",
        });
        invalidateQuery([cachedAPIName.USER_TASK_EXECUTION]);
      },
      onError: () => {
        showAlert({
          title: t('errorMessages.globalSnackBarMessage'),
          type: "error",
        });
      },
    });
    setIsPopoverOpen(false);
  };

  useEffect(() => {
    const handleOutsideClick = (event: any) => {
      const popover = document.getElementById("popover");
      if (popover && !popover.contains(event.target)) {
        setIsPopoverOpen(false);
      }
    };

    if (isPopoverOpen) {
      document.addEventListener("click", handleOutsideClick);
    }

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [isPopoverOpen]);

  return (
    <>
      {isListView ? (
        <div
          className="py-4 px-8 border border-gray-light rounded-md mb-2 w-full relative"
          onClick={enabled ? onClick : () => {}}
        >
          <div className="flex items-center gap-2">
            <div
              className="text-gray-dark group-hover:text-gray-darker"
              aria-hidden="true"
            >
              {icon}
            </div>
            <h3 className="text-subtitle8 text-gray-dark hover:cursor-pointer">
              {title}
            </h3>
          </div>
          <p className="mt-1 text-[16px] text-gray-lighter hover:cursor-pointer">{description}</p>
          <div className="flex items-center gap-2 mt-2 text-subtitle3 hover:cursor-pointer">
            <span>{timeAgo}</span>
            <span>{task?.produced_text_production && "✓"}</span>
          </div>
          <>
            <EllipsisVerticalIcon
              className="absolute right-[12px] top-[15px] h-5 w-5 text-gray-lighter cursor-pointer text-xs"
              aria-hidden="true"
              onClick={(e) => {
                e.stopPropagation();
                setIsPopoverOpen(!isPopoverOpen);
              }}
            />

            {isPopoverOpen && (
              <div
                id="popover"
                className="absolute right-[28px] top-[30px] bg-white border p-2 rounded-[4px] text-sm text-gray-lighter cursor-pointer"
                onClick={() =>
                  onDeleteUserTaskExecution(task?.user_task_execution_pk)
                }
              >
                <FontAwesomeIcon icon={faTrash} />
                <button className="ml-2 font-semibold">{t("userTaskExecutionList.removeButton")}</button>
              </div>
            )}
          </>
        </div>
      ) : (
        <div className={containerClassName}>
          {showActions && (
            <>
              <EllipsisVerticalIcon
                className="absolute right-[12px] top-[15px] h-5 w-5 text-gray-lighter cursor-pointer text-xs"
                aria-hidden="true"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsPopoverOpen(!isPopoverOpen);
                }}
              />

              {isPopoverOpen && (
                <div
                  id="popover"
                  className="absolute right-[28px] top-[30px] bg-white border p-2 rounded-[4px] text-sm text-gray-lighter cursor-pointer"
                  onClick={() =>
                    onDeleteUserTaskExecution(task?.user_task_execution_pk)
                  }
                >
                  <FontAwesomeIcon icon={faTrash} />
                  <button className="ml-2 font-semibold">Remove</button>
                </div>
              )}
            </>
          )}
            <div onClick={enabled ? onClick : () => {}}>
            <div
              className="text-gray-dark group-hover:text-gray-darker mb-2"
              aria-hidden="true"
            >
              {icon}
            </div>
            <div className="mt-1">
              <div className="flex items-center">
                {(task?.n_not_read_todos || 0) > 0 && (
                  <div className="h-2 w-2 rounded-full bg-blue-600 absolute left-1"></div>
                )}
                <h3 className="text-subtitle8 text-gray-dark hover:cursor-pointer">
                  {title}
                </h3>
              </div>
              <p className="mt-2 text-subtitle3 text-gray-lighter">
                {description}
              </p>
            </div>
            {showActions && (
              <div className="flex items-center gap-2 mt-3 text-subtitle3">
                <span>{timeAgo}</span>
                <span>{task?.produced_text_production && "✓"}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default TaskCard;
