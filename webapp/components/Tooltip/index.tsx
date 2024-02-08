import { FC, ReactNode, useRef } from "react";

interface Props {
    children: ReactNode;
    tooltip?: string;
    size?: string;
}

const ToolTip: FC<Props> = ({ children, tooltip, size }): JSX.Element => {
    const tooltipRef = useRef < HTMLSpanElement > (null);
    const container = useRef < HTMLDivElement > (null);
    if (!size) 
        size = "fit";

    return (
        <div
            ref={container}
            onMouseEnter={({ clientX }) => {
                if (!tooltipRef.current || !container.current) return;
                const { left } = container.current.getBoundingClientRect();

                tooltipRef.current.style.left = clientX - left + "px";
            }}
            className="group relative inline-block"
        >
            {children}
            {tooltip ? (
                <span
                    ref={tooltipRef}
                    className={`invisible group-hover:visible ${"w-" + size} opacity-0 group-hover:opacity-100 transition text-xs bg-gray-600 text-gray-200 p-1 rounded absolute top-full whitespace-normal break-words`}
                >
                    {tooltip}
                </span>
            ) : null}
        </div>
    );
};

export default ToolTip;