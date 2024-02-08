import { useCallback, useContext, useEffect, Fragment, useState } from "react";
import { useRouter } from "next/router";
import Image from "next/image";
import { Dialog, Transition } from "@headlessui/react";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { getSession, useSession } from "next-auth/react";
import Sidebar from "components/Layout/Sidebar";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import { SessionType } from "helpers/interface/session";
import useLanguageCode from "helpers/hooks/useLanguageCode";
import useTimezone from "helpers/hooks/useTimezone";
import useGetAllTodos from "modules/Tasks/hooks/useGetAllTodos";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const router = useRouter();
  const { data: sessionData } = useSession() as { data: SessionType | null };
  const { globalState, setGlobalState } = useContext(
    globalContext
  ) as GlobalContextType;
  const { session } = globalState || {};
  const languageCode = useLanguageCode();
  const timezone = useTimezone();
  const { data: todos } = useGetAllTodos();

  const [showUnreadTodo, setShowUnreadTodo] = useState(false);

  useEffect(() => {
    if (todos?.n_todos_not_read && !showUnreadTodo) setShowUnreadTodo(true);
  }, [todos]);

  const userLanguageCode = () => {
    const selectedLanguageCode: any = sessionData?.authorization?.language_code
      ? sessionData?.authorization?.language_code
      : router.locale;

    languageCode.mutate({ language_code: selectedLanguageCode });
    localStorage.setItem("language_code", selectedLanguageCode);
  };

  const userTimezoneSet = () => {
    const currentDatetime: Date = new Date();
    const timezoneOffset: string = currentDatetime
      .getTimezoneOffset()
      .toString();

    timezone.mutate({ timezone_offset: timezoneOffset });
  };

  useEffect(() => {
    if (sessionData) {
      setGlobalState({ session: sessionData });
    }
  }, [sessionData]);

  useEffect(() => {
    if (
      sessionData &&
      localStorage.getItem("language_code") !== router.locale
    ) {
      userTimezoneSet();
      userLanguageCode();

      const languageCodeToUse =
        sessionData.authorization?.language_code || router.locale;

      router.push(router.pathname, router.pathname, {
        locale: languageCodeToUse,
      });
    }
  }, [sessionData, router.locale]);

  const getSessionHandler = useCallback(async () => {
    const session = (await getSession()) as SessionType | null;
    if (session) {
      setGlobalState({ session });
    } else {
      router.push("/auth/signin");
    }
  }, []);

  useEffect(() => {
    getSessionHandler();
  }, [getSessionHandler]);

  if (!session) {
    return null;
  }

  return (
    <>
      <div>
        <Transition.Root show={sidebarOpen} as={Fragment}>
          <Dialog
            as="div"
            className="relative z-50 lg:hidden"
            onClose={setSidebarOpen}
          >
            <Transition.Child
              as={Fragment}
              enter="transition-opacity ease-linear duration-300"
              enterFrom="opacity-0"
              enterTo="opacity-100"
              leave="transition-opacity ease-linear duration-300"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <div className="fixed inset-0 bg-gray-900/80" />
            </Transition.Child>

            <div className="fixed inset-0 flex">
              <Transition.Child
                as={Fragment}
                enter="transition ease-in-out duration-300 transform"
                enterFrom="-translate-x-full"
                enterTo="translate-x-0"
                leave="transition ease-in-out duration-300 transform"
                leaveFrom="translate-x-0"
                leaveTo="-translate-x-full"
              >
                <Dialog.Panel className="relative mr-16 flex w-full max-w-[250px] flex-1">
                  <Transition.Child
                    as={Fragment}
                    enter="ease-in-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in-out duration-300"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                  >
                    <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                      <button
                        type="button"
                        className="-m-2.5 p-2.5"
                        onClick={() => setSidebarOpen(false)}
                      >
                        <span className="sr-only">Close sidebar</span>
                        <XMarkIcon
                          className="h-6 w-6 text-white"
                          aria-hidden="true"
                        />
                      </button>
                    </div>
                  </Transition.Child>
                  {/* Sidebar component, swap this element with another sidebar if you like */}
                  <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-darker px-6 pb-2">
                    <Sidebar />
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </Dialog>
        </Transition.Root>

        {/* Static sidebar for desktop */}
        <div className="overflow-hidden hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-[250px] lg:flex-col">
          <div className="flex grow flex-col gap-y-5 bg-gray-darker px-5">
            <Sidebar />
          </div>
        </div>

        <div className="sticky top-0 z-40 flex items-center gap-x-6 bg-gray-darker px-4 py-4 shadow-sm sm:px-6 lg:hidden">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-indigo-200 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            {showUnreadTodo && (
              <div className="h-2 w-2 rounded-full bg-blue-600 absolute left-9 top-4 sm:left-[50px]" />
            )}
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex flex-1 justify-end">
            <Image
              className="h-8 w-8 rounded-full"
              src={
                session?.user?.image
                  ? session.user.image
                  : "/images/default_user.png"
              }
              alt=""
              width={60}
              height={60}
            />
          </div>
        </div>

        <main className="lg:pl-[250px]">
          <div className="h-[calc(100vh-72px)] lg:h-screen overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </>
  );
};

export default Layout;
