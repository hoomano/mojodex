import { classNames } from "helpers/method";

interface PillsType {
  className?: string;
  children: React.ReactNode;
  type:
    | "primary"
    | "primary-light"
    | "primary-lighter"
    | "gray-dark"
    | "gray-lighter"
    | "gray-light"
    | "gray-light-secondary";
  onClick?: () => void;
  size?: "large" | "middle" | "small";
  disabled?: boolean;
  href?: string;
}

const Pills = ({
  children,
  className,
  size = "middle",
  disabled = false,
  type = "primary",
}: PillsType) => {
  let classes = "rounded-full";
  if (type === "primary") {
    classes += " bg-primary-main text-white";
  } else if (type === "primary-light") {
    classes += " bg-primary-light text-primary-dark";
  } else if (type === "primary-lighter") {
    classes += " bg-gray-light text-primary-main";
  } else if (type === "gray-dark") {
    classes += " bg-gray-dark text-white";
  } else if (type === "gray-lighter") {
    classes += " bg-gray-lighter text-gray-darker";
  } else if (type === "gray-light") {
    classes += " bg-gray-light text-black";
  } else if (type === "gray-light-secondary") {
    classes += " bg-gray-light text-gray-darker";
  }

  if (size === "large") {
    classes += "  py-3 text-subtitle6 px-6";
  } else if (size === "middle") {
    classes += "  py-2 text-subtitle6 px-4";
  } else if (size === "small") {
    classes += "  py-1 text-subtitle2 px-3";
  }

  return (
    <button className={classNames(className, classes)} disabled={disabled}>
      {children}
    </button>
  );
};

export default Pills;
