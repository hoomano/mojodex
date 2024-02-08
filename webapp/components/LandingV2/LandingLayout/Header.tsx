import { useState } from "react";
import Link from "next/link";
import { Popover } from "@headlessui/react";
import { AnimatePresence, motion } from "framer-motion";
import Button from "components/Button";
import { Container } from "../common/Container";
import { useRouter } from "next/router";
import { useSession } from "next-auth/react";
import Modal from "components/Modal";
import { XMarkIcon } from "@heroicons/react/24/outline";

function MenuIcon(props: React.ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <path
        d="M5 6h14M5 18h14M5 12h14"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChevronUpIcon(props: React.ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      <path
        d="M17 14l-5-5-5 5"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MobileNavLink(
  props: Omit<
    React.ComponentPropsWithoutRef<typeof Popover.Button<typeof Link>>,
    "as" | "className"
  >
) {
  return (
    <Popover.Button
      as={Link}
      className="block text-base leading-7 tracking-tight text-gray-700"
      {...props}
    />
  );
}

export function Header() {
  const [isSignupModalOpen, setIsSignupModalOpen] = useState(false);
  const router = useRouter();
  const session = useSession();

  const handleLanguageChange = (e: any) => {
    router.push(router.pathname, router.pathname, { locale: e.target.value });
  };

  return (
    <header>
      <nav>
        <Container className="relative z-50 flex justify-between items-center h-[100px]">
          <div className="relative z-10 flex items-center gap-16">
            <Link href="/" aria-label="Home">
              <img
                className="max-w-[150px]"
                src="/images/logo/hoomano_logo.png"
                alt="Mojodex"
              />
            </Link>
          </div>
          <div className="flex items-center gap-6">
            <Popover className="lg:hidden">
              {({ open }) => (
                <>
                  <Popover.Button
                    className="relative z-10 -m-2 inline-flex items-center rounded-lg stroke-gray-900 p-2 hover:bg-gray-200/50 hover:stroke-gray-600 active:stroke-gray-900 ui-not-focus-visible:outline-none"
                    aria-label="Toggle site navigation"
                  >
                    {({ open }) =>
                      open ? (
                        <ChevronUpIcon className="h-6 w-6" />
                      ) : (
                        <MenuIcon className="h-6 w-6" />
                      )
                    }
                  </Popover.Button>
                  <AnimatePresence initial={false}>
                    {open && (
                      <>
                        <Popover.Overlay
                          static
                          as={motion.div}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="fixed inset-0 z-0 bg-gray-300/60 backdrop-blur"
                        />
                        <Popover.Panel
                          static
                          as={motion.div}
                          initial={{ opacity: 0, y: -32 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{
                            opacity: 0,
                            y: -32,
                            transition: { duration: 0.2 },
                          }}
                          className="absolute inset-x-0 top-0 z-0 origin-top rounded-b-2xl bg-gray-50 px-6 pb-6 pt-32 shadow-2xl shadow-gray-900/20"
                        >
                          {session?.status === "authenticated" ? (
                            <Button
                              onClick={() => router.push("/tasks")}
                              variant="outline"
                            >
                              Go to Task
                            </Button>
                          ) : (
                            <div className="mt-6">
                              <select
                                className="rounded py-[3px] pl-2 hidden lg:block"
                                value={router.locale}
                                onChange={handleLanguageChange}
                              >
                                <option value="en">EN</option>
                                <option value="fr">FR</option>
                              </select>
                              <Button
                                onClick={() => router.push("/auth/signup")}
                                className="flex w-full items-center justify-center"
                              >
                                Sign Up
                              </Button>

                              <p className="mt-6 text-center text-base font-medium text-gray-500">
                                Existing customer?
                                <a
                                  href="/auth/signin"
                                  className="text-primary-main hover:text-primary-main"
                                >
                                  &nbsp;Sign in
                                </a>
                              </p>
                            </div>
                          )}
                          <select
                            className="rounded py-[3px] pl-2 lg:block"
                            value={router.locale}
                            onChange={handleLanguageChange}
                          >
                            <option value="en">EN</option>
                            <option value="fr">FR</option>
                          </select>
                        </Popover.Panel>
                      </>
                    )}
                  </AnimatePresence>
                </>
              )}
            </Popover>

            {session?.status === "authenticated" && (
              <Button
                onClick={() => router.push("/tasks")}
                variant="outline"
                className="hidden lg:block"
              >
                Go to Task
              </Button>
            )}

            {session?.status === "unauthenticated" && (
              <>
                <select
                  className="rounded py-[3px] pl-2 hidden lg:block"
                  value={router.locale}
                  onChange={handleLanguageChange}
                >
                  <option value="en">EN</option>
                  <option value="fr">FR</option>
                </select>
                <Button
                  onClick={() => router.push("/auth/signin")}
                  className="hidden lg:block"
                  variant="outline"
                >
                  Login
                </Button>
                <Button
                  onClick={() => router.push("/auth/signup")}
                  className="hidden lg:block"
                >
                  Sign Up
                </Button>
              </>
            )}
            <Modal
              isOpen={isSignupModalOpen}
              footerPresent={false}
              headerPresent={false}
              widthClass="max-w-[480px]"
            >
              <div className="p-[40px]">
                <XMarkIcon
                  className="h-6 w-6 text-gray-lighter absolute right-5 top-5 cursor-pointer"
                  aria-hidden="true"
                  onClick={() => setIsSignupModalOpen(false)}
                />

                <div>
                  <h2 className="text-[40px] font-[900] uppercase text-center leading-10">
                    Get the mojodex app
                  </h2>
                  <p className="text-lg text-center mt-2">
                    Scan the QR code to download the app
                  </p>
                  <img
                    className="m-auto p-8"
                    src="images/qr_code.png"
                    alt="qr_code"
                  />
                </div>
              </div>
            </Modal>
          </div>
        </Container>
      </nav>
    </header>
  );
}
