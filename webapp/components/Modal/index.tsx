import { Dialog, Transition } from "@headlessui/react";
import Button from "components/Button";
import { classNames } from "helpers/method";
import React, { Fragment, useState } from "react";

interface ModalType {
  isOpen: boolean;
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
  headerPresent?: boolean;
  footerPresent?: boolean;
  widthClass?: string;
}

const Modal = ({
  isOpen,
  title,
  headerPresent = true,
  footerPresent = true,
  onClose,
  children,
  widthClass,
}: ModalType) => {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-50"
        onClose={() => onClose && onClose()}
      >
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel
                className={classNames(
                  "w-full transform overflow-hidden rounded-xl bg-white text-left align-middle shadow-xl transition-all border border-gray-lighter",
                  widthClass
                )}
              >
                {headerPresent && (
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900 p-4 border-b border-gray-lighter"
                  >
                    {title}
                  </Dialog.Title>
                )}
                <div className="border-b border-gray-lighter">
                  {children}
                </div>
                {footerPresent && (
                  <div className="p-4 flex justify-end">
                    <Button
                      variant="gray-dark"
                      size="middle"
                      onClick={onClose}
                      className="mr-2"
                    >
                      Close
                    </Button>
                    <Button variant="primary" size="middle" onClick={onClose}>
                      Save Changes
                    </Button>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default Modal;
