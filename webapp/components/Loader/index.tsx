import { BeatLoader } from "react-spinners";

const Loader = ({ color = "#6366F1" }) => {
  return (
    <div className="flex justify-center items-center w-full py-6">
      <BeatLoader color={color} />
    </div>
  );
};

export default Loader;
