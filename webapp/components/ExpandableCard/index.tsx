import React, { useState, FunctionComponent, ReactNode } from 'react';
import {
    ChevronDownIcon,
    ChevronUpIcon,
} from "@heroicons/react/24/outline";


interface ExpandableCardProps {
    headerText: string;
    children: ReactNode;
}


const ExpandableCard: FunctionComponent<ExpandableCardProps> = ({ headerText, children }) => {

    // State to manage the expand/collapse of the card
    const [isCardExpanded, setIsCardExpanded] = useState(false);

    // Function to toggle the card's expanded state
    const toggleCard = () => {
        setIsCardExpanded(!isCardExpanded);
    };


    return (
        <div className="border mb-3 p-2 rounded-lg border-gray-light">
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => {
                    setIsCardExpanded(!isCardExpanded);
                }}
            >
                <div className="flex items-center gap-3">
                    <div className="text-subtitle3 text-gray-darker">
                        {headerText}
                    </div>
                </div>
                <div className="text-subtitle3 flex gap-3 text-gray-lighter">
                    {
                        (isCardExpanded ? (
                            <ChevronUpIcon className="w-[24px] h-[24px] mr-2" />
                        ) : (
                            <ChevronDownIcon className="w-[24px] h-[24px] mr-2" />
                        ))}
                </div>
            </div>
            {isCardExpanded ? children : null}
        </div>
    
  );

};

export default ExpandableCard;