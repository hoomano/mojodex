import { FaSms } from "react-icons/fa";

const IPhoneTextButton = ({ message }: { message: string | undefined }) => {
  const handleButtonClick = () => {
    const recipient = "";

    const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
    const isMac = /Macintosh/.test(navigator.userAgent);

    if ((isIOS || isMac) && message) {
      const url = `sms:${recipient}&body=${encodeURIComponent(message)}`;
      window.location.href = url;
    }
  };

  return (
    <div>
      {/iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) && (
        <button onClick={handleButtonClick}>
          <FaSms size={32} className="text-gray-500" />
        </button>
      )}
    </div>
  );
};

export default IPhoneTextButton;
