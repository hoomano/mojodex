import { Switch } from "@headlessui/react";
import { classNames } from "helpers/method";
import { TaskPreference } from "modules/Tasks/interface";
import React, { Dispatch, SetStateAction } from "react";

interface Props {
  isLoading: boolean;
  preferences: (TaskPreference & { enabled: boolean })[];
  setPreferences: Dispatch<
    SetStateAction<
      (TaskPreference & {
        enabled: boolean;
      })[]
    >
  >;
}

const PrefSwitchGroup = ({ isLoading, preferences, setPreferences }: Props) => {
  const changeStatePreference = (preferencePk: number) => {
    setPreferences((prev) =>
      prev.map((preference) => {
        if (preference.user_task_preference_pk === preferencePk) {
          return {
            ...preference,
            enabled: !preference.enabled,
          };
        }
        return preference;
      })
    );
  };

  return (
    <Switch.Group as="div" className="px-4 py-1 sm:p-6">
      <ul role="list" className="grid-cols-1 mx-10 py-3">
        {!isLoading &&
          (preferences?.length ? (
            preferences.map(({ user_task_preference_pk, enabled, name }) => (
              <li key={user_task_preference_pk}>
                <div className="mt-2 sm:flex sm:items-start sm:justify-between">
                  <div className="max-w-xl text-sm text-gray-500">
                    <Switch.Description>{name}</Switch.Description>
                  </div>
                  <div className="mt-5 sm:ml-6 sm:mt-0 sm:flex sm:flex-shrink-0 sm:items-center">
                    <Switch
                      checked={enabled}
                      onChange={() =>
                        changeStatePreference(user_task_preference_pk)
                      }
                      className={classNames(
                        enabled ? "bg-indigo-600" : "bg-gray-200",
                        "relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
                      )}
                    >
                      <span
                        aria-hidden="true"
                        className={classNames(
                          enabled ? "translate-x-5" : "translate-x-0",
                          "inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                        )}
                      />
                    </Switch>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <div className="text-center text-gray-600">
              Nothing to display here yet !
            </div>
          ))}
      </ul>
    </Switch.Group>
  );
};

export default PrefSwitchGroup;
