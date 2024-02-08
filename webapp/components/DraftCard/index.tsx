import { faClose, faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import ToolTip from "components/Tooltip";

interface DraftCardProps {
  isNewLabel?: boolean;
  icon: string;
  title: string;
  tooltipInfo?: string;
  showDelete?: boolean;
  creationDate: string;
  definition: string;
  onDeleteClick?: (event: React.MouseEvent<HTMLElement>) => void;
  onCardClick: () => void;
}

const DraftCard = ({
  isNewLabel = false,
  icon = "",
  title,
  tooltipInfo = "",
  showDelete = false,
  creationDate = "",
  definition = "",
  onDeleteClick = () => {},
  onCardClick,
}: DraftCardProps) => {
  return (
    <div
      className="rounded-xl border border-gray-200 mb-5 hover:bg-gray-200 hover:cursor-pointer"
      onClick={onCardClick}
    >
      <div
        id="card"
        className="flex rounded-t-xl items-center gap-x-4 border-b border-gray-900/5 py-2 px-6"
      >
        <img
          src={"/images/alfred.png"}
          className="h-5 flex-none rounded-lg bg-white object-cover ring-1 ring-gray-900/10"
        />
        {isNewLabel ? (
          <span className="inline-flex float-right items-center gap-x-1.5 rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-600">
            <svg
              className="h-1.5 w-1.5 fill-blue-400"
              viewBox="0 0 6 6"
              aria-hidden="true"
            >
              <circle cx={3} cy={3} r={3} />
            </svg>
            New
          </span>
        ) : null}
        <div className="text-sm leading-6 text-gray-700">
          {icon} &nbsp; {title}
        </div>

        {!!tooltipInfo && (
          <div>
            <sup>
              <ToolTip size="80" tooltip={tooltipInfo}>
                <FontAwesomeIcon
                  icon={faInfoCircle}
                  className="text-gray-800"
                />
              </ToolTip>
            </sup>
          </div>
        )}

        {showDelete && (
          <button
            id="delete"
            className="flex flex-grow justify-end items-start"
            onClick={onDeleteClick}
          >
            <FontAwesomeIcon
              icon={faClose}
              className="text-gray-400 h-5 hover:text-gray-700 hover:cursor-pointer hover:scale-125 transform transition"
            />
          </button>
        )}
      </div>
      <dl className="-my-3 divide-y divide-gray-100 px-6 py-4 text-sm leading-6">
        <div className="flex-col py-5">
          <dd className="flex items-start gap-x-2">
            <div className="text-gray-900">{definition}</div>
          </dd>
          <dd className="text-gray-400 float-right pb-5">
            <div>{creationDate}</div>
          </dd>
        </div>
      </dl>
    </div>
  );
};

export default DraftCard;
