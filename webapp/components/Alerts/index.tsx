import Icon from "components/Icon";
import { classNames } from "helpers/method";

export interface Alert {
  className?: string;
  title: React.ReactNode;
  type: "primary" | "secondary" | "success" | "warning" | "error";
  onClose?: () => void;
  show: boolean;
}

const Alerts = ({
  title,
  className,
  type = "primary",
  show = false,
  onClose,
}: Alert) => {
  let classes =
    "flex justify-between rounded-md p-4 w-[295px] text-subtitle2 items-center";
  let warningIconName = "triangle_warning_primary";
  let closeIconName = "close_primary";

  if (type === "primary") {
    classes +=
      " bg-primary-light text-primary-dark border border-primary-light";
    warningIconName = "triangle_warning_primary";
    closeIconName = "close_primary";
  } else if (type === "secondary") {
    classes += " bg-grey-light text-black border border-gray-lighter";
    warningIconName = "triangle_warning_dark";
    closeIconName = "close_dark";
  } else if (type === "success") {
    classes +=
      " bg-success-secondary text-success-primary border border-success-secondary";
    warningIconName = "circle_check";
    closeIconName = "close_success";
  } else if (type === "warning") {
    classes +=
      " bg-warning-secondary text-warning-primary border border-warning-secondary";
    warningIconName = "triangle_warning_danger";
    closeIconName = "close_danger";
  } else if (type === "error") {
    classes +=
      " bg-error-secondary text-error-primary border border-error-secondary";
    warningIconName = "triangle_warning_danger";
    closeIconName = "close_danger";
  }

  return (
    <div className={classNames(className, "alert", classes, show && "show")}>
      <Icon
        className="mr-2"
        iconName={warningIconName}
        width={16}
        height={16}
      />
      <div className="flex-1">{title}</div>
      <Icon
        className="cursor-pointer"
        iconName={closeIconName}
        width={16}
        height={16}
        onClick={onClose}
      />
    </div>
  );
};

export default Alerts;
