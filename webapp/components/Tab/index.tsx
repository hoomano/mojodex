import { Tab } from "@headlessui/react";
import { classNames } from "helpers/method";
import { useMemo } from "react";

export interface TabType {
  key: string;
  title: string;
  component: React.ReactNode;
}

interface TabComponentType {
  tabs: TabType[];
  selected: string;
  onChangeTab: (key: string) => void;
  isDisable?: boolean;
  notReadTodos?: number;
}

const TabComponent = ({
  tabs = [],
  selected,
  onChangeTab,
  isDisable,
  notReadTodos,
}: TabComponentType) => {
  const selectedIndex = useMemo(() => {
    return tabs.findIndex((tab) => tab.key === selected);
  }, [selected, tabs]);

  const onChangeTabHandler = (index: number) => {
    if (isDisable) {
      return;
    }
    onChangeTab(tabs[index].key);
  };
  return (
    <div className="-ml-3">
      <Tab.Group
        selectedIndex={selectedIndex}
        manual
        onChange={onChangeTabHandler}
      >
        <Tab.List className="flex">
          {tabs.map((tab) => {
            return (
              <Tab
                key={tab.key}
                className={({ selected }) =>
                  classNames(
                    "outline-0 px-3 relative",
                    selected ? "text-gray-darker" : "text-gray-lighter",
                    isDisable ? "cursor-not-allowed" : ""
                  )
                }
              >
                {tab.title === "Todos" && (notReadTodos || 0) > 0 && (
                  <div className="bg-blue-600 text-white text-[14px] w-5 h-5 rounded-full absolute right-0 top-[-16px]">
                    {notReadTodos}
                  </div>
                )}
                {tab.title}
                <div
                  className={classNames(
                    "m-auto max-w-[50%] h-1",
                    selected === tab.key && "border-b-2 border-primary-main"
                  )}
                ></div>
              </Tab>
            );
          })}
        </Tab.List>
        <Tab.Panels className="mt-2">
          {tabs.map((tab) => {
            return (
              <Tab.Panel key={tab.key} className={classNames("")}>
                {tab.component}
              </Tab.Panel>
            );
          })}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};

export default TabComponent;
