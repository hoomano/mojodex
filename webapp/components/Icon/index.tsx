import Image from "next/image";

interface IconType {
  iconName: string;
  width?: number;
  height?: number;
  className?: string;
  onClick?: () => void;
}

const Icon = ({
  iconName,
  width = 24,
  height = 24,
  className,
  onClick,
}: IconType) => {
  return (
    <Image
      src={`/images/icons/${iconName}.svg`}
      width={width}
      height={height}
      alt="icon"
      style={{ color: "chartreuse" }}
      className={className}
      onClick={onClick}
    ></Image>
  );
};

export default Icon;
