import React, { useContext, useEffect, useState } from "react";
import { useRouter } from "next/router";
import useContextSession from "helpers/hooks/useContextSession";
import Image from "next/image";
import { signOut } from "next-auth/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSignOut } from "@fortawesome/free-solid-svg-icons";
import {
  // ChatBubbleLeftIcon,
  // PencilIcon,
  Squares2X2Icon,
  ChevronDownIcon,
  BookmarkIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
// import ChatHistory from "modules/Chat/components/ChatHistory";
import useGetChatHistory from "modules/Chat/hooks/useGetChatHistory";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";
import useGetAllTodos from "modules/Tasks/hooks/useGetAllTodos";
import { useTranslation } from "react-i18next";

declare let window: {
  chrome: any;
  postMessage: any;
  location: any;
};

declare let chrome: {
  runtime: any;
};

const Sidebar = () => {
  const session = useContextSession();
  const router = useRouter();
  const sessionId = router.query?.sessionId as string;
  const [isDropdownOpen, setIsDropdownOpen] = useState(!!sessionId);
  const { globalState } = useContext(globalContext) as GlobalContextType;
  useGetChatHistory();
  const editorExtensionId = process.env.NEXT_PUBLIC_EDITOR_EXTENSION_ID;
  const { data: todos } = useGetAllTodos();
  const { t } = useTranslation("dynamic");

  const [showUnreadTodo, setShowUnreadTodo] = useState(false);

  useEffect(() => {
    if (todos?.n_todos_not_read) {
      setShowUnreadTodo(true);
    } else if (router.asPath === "/tasks") {
      setShowUnreadTodo(false);
    }
  }, [todos, router]);

  const classNames = (...classes: string[]) => {
    return classes.filter(Boolean).join(" ");
  };

  const checkRouteActive = (routeName: string) => {
    if (routeName === "/") {
      return routeName === router.pathname;
    } else {
      return router.pathname.includes(routeName);
    }
  };

  const navigation: {
    name: string;
    href: string;
    icon: any;
    component?: React.ReactElement;
    onClick?: Function;
  }[] = [
    {
      name: `${t("appDrawer.taskListButton")}`,
      href: "/tasks",
      icon: Squares2X2Icon,
    },
    // {
    //   name: "Chat",
    //   href: "/",
    //   icon: ChatBubbleLeftIcon,
    //   component: <ChatHistory />,
    // },
    // { name: "Drafts", href: "/drafts", icon: PencilIcon },
    {
      name: `${t("appDrawer.resourcesButton")}`,
      href: "/resources",
      icon: BookmarkIcon,
    },
    {
      name: `${t("appDrawer.todosButton")}`,
      href: "/todos",
      icon: CheckCircleIcon,
    },
  ];

  const onNavigationClick = (item: any) => {
    router.push(item.href);
  };

  return (
    <>
      <div
        className="flex h-16 shrink-0 items-center cursor-pointer"
        onClick={() => router.push("/")}
      >
        <img
          className="h-8 w-auto"
          src="/images/logo/mojodex_logo.png"
          alt="Mojodex"
        />
        <p className="text-lg text-white font-bold">
          &nbsp; {t("appDrawer.title")} &nbsp;
        </p>
      </div>
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="space-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <button
                    onClick={() => onNavigationClick(item)}
                    className={classNames(
                      checkRouteActive(item.href)
                        ? "bg-primary-main text-white"
                        : "text-indigo-200 hover:text-white hover:bg-primary-main",
                      "group flex items-center justify-between gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold w-full"
                    )}
                  >
                    <div className="flex items-center gap-4 text-start">
                      {item.name === "Todos" && showUnreadTodo && (
                        <div className="h-2 w-2 rounded-full bg-blue-600 absolute left-2" />
                      )}
                      <item.icon
                        className={classNames(
                          checkRouteActive(item.href)
                            ? "text-white"
                            : "text-indigo-200 group-hover:text-white",
                          "h-5 w-5 shrink-0 text-start"
                        )}
                        aria-hidden="true"
                      />
                      {item.name}
                    </div>
                    {item?.component && (
                      <ChevronDownIcon
                        className={classNames(
                          checkRouteActive(item.href)
                            ? "text-white"
                            : "text-indigo-200 group-hover:text-white",
                          "h-4 w-4 shrink-0"
                        )}
                        aria-hidden="true"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsDropdownOpen(!isDropdownOpen);
                          globalState?.mainChatInputRef?.focus();
                        }}
                      />
                    )}
                  </button>
                  {isDropdownOpen && item?.component}
                </li>
              ))}
            </ul>
          </li>
          <li className="-mx-6 mt-auto">
            <div className="flex items-center gap-x-4 px-6 py-3 text-sm font-semibold leading-6 text-white">
              <Image
                className="h-8 w-8 rounded-full cursor-pointer"
                src={
                  session?.user?.image
                    ? session.user.image
                    : "/images/default_user.png"
                }
                alt=""
                width={60}
                height={60}
                onClick={() => router.push("/settings")}
              />
              <span
                className="flex-1 text-subtitle4 break-all cursor-pointer"
                aria-hidden="true"
                onClick={() => router.push("/settings")}
              >
                {session?.authorization?.name}
              </span>
              <div
                onClick={() => {
                  const editorExtensionId = process.env.NEXT_PUBLIC_EDITOR_EXTENSION_ID;

                  if (editorExtensionId && window?.chrome?.runtime?.sendMessage) {
                    chrome.runtime.sendMessage(editorExtensionId, {
                      message: {
                        isLogin: false,
                      },
                    });
                  }
                  localStorage.removeItem("language_code");
                  signOut();
                }}
              >
                <FontAwesomeIcon
                  icon={faSignOut}
                  className="text-white cursor-pointer"
                />
              </div>
            </div>
          </li>
        </ul>
      </nav>
    </>
  );
};

export default Sidebar;
