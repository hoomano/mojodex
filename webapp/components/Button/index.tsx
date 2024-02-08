import { classNames } from "helpers/method";

interface ButtonType {
  className?: string;
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "link" | "outline" | "gray-dark";
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  size?: "large" | "middle" | "small";
  disabled?: boolean;
  href?: string;
  type?: "button" | "submit" | "reset";
  isLoading?: boolean;
  loadingText?: string;
}

const Button = ({
  children,
  className,
  size = "middle",
  disabled = false,
  variant = "primary",
  type = "button",
  isLoading = false,
  onClick,
  loadingText,
}: ButtonType) => {
  let classes = "rounded-md border border-transparent disabled:opacity-70";
  if (variant === "primary") {
    classes += ` bg-primary-main text-white ${
      isLoading && "flex m-auto gap-2.5"
    }`;
  } else if (variant === "outline") {
    classes += " text-primary-main border border-primary-main";
  } else if (variant === "secondary") {
    classes += " text-primary-main bg-gray-light";
  } else if (variant === "gray-dark") {
    classes += " text-white bg-gray-dark";
  } else if (variant === "link") {
    classes += " text-primary-main";
  }

  if (size === "large") {
    classes += "  py-3 text-subtitle6 px-6";
  } else if (size === "middle") {
    classes += "  py-2 text-subtitle6 px-4";
  } else if (size === "small") {
    classes += "  py-1 text-subtitle2 px-3";
  }

  return (
    <button
      type={type}
      className={classNames(className, classes, "relative")}
      disabled={disabled || isLoading}
      onClick={onClick}
    >
      {isLoading && <div className="button-loader"></div>}
      {isLoading ? loadingText || children : children}
    </button>
  );
};

export default Button;
