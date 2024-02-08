interface Props {
  onClick?: () => void;
  name?: string;
  icon?: string;
  definition?: string;
}

const Card = ({ onClick, name, icon, definition }: Props) => (
  <button
    className="w-full flex flex-col justify-center items-center gap-[20px] border border-gray-medium rounded-lg p-5"
    onClick={onClick}
  >
    <div className="text-[26px]">{icon}</div>
    <h5 className="text-h5">{name}</h5>
    <p className="text-subtitle5 text-gray-lighter text-center">{definition}</p>
  </button>
);

export default Card;
