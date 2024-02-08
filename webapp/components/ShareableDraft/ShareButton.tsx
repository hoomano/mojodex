import React from "react";
import { Fragment } from "react";
import { Menu, Transition } from "@headlessui/react";
import { FaShareAlt } from "react-icons/fa"; // Import the send icon from the Font Awesome library
import {
  TwitterShareButton,
  TelegramShareButton,
  WhatsappShareButton,
  EmailShareButton,
  TwitterIcon,
  TelegramIcon,
  WhatsappIcon,
  EmailIcon,
} from "react-share";
import IPhoneTextButton from "./IPhoneTextButton";

const ShareButton = ({ message }: { message: string | undefined }) => {
  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button title="Share">
          <FaShareAlt className="text-white w-3.5 h-3.5 mt-2" />
          {/* <ChevronDownIcon className="-mr-1 h-5 w-5 text-gray-400" aria-hidden="true" /> */}
        </Menu.Button>
      </div>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-10 mt-1 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="py-1">
            <Menu.Item>
              {() => (
                <a>
                  <div className="flex justify-center items-center">
                    <TwitterShareButton
                      url="https://hoomano.com/mojodex"
                      title={message + " - Assisted by @MojodexApp"}
                      className="ml-1 mr-1"
                    >
                      <TwitterIcon size={32} round />
                    </TwitterShareButton>
                  </div>

                  <div className="flex justify-center items-center">
                    <TelegramShareButton
                      url="https://hoomano.com/mojodex"
                      title={
                        message + " - Assisted by #Mojodex @HoomanoCompany"
                      }
                      className="ml-1 mr-1"
                    >
                      <TelegramIcon size={32} round />
                    </TelegramShareButton>
                  </div>

                  <div className="flex justify-center items-center">
                    <WhatsappShareButton
                      url="https://hoomano.com/mojodex"
                      title={
                        message + " - Assisted by #Mojodex @HoomanoCompany"
                      }
                      separator=":: "
                      className="ml-1 mr-1"
                    >
                      <WhatsappIcon size={32} round />
                    </WhatsappShareButton>
                  </div>

                  <div className="flex justify-center items-center">
                    <EmailShareButton
                      url="https://hoomano.com/mojodex"
                      subject=""
                      body={message + "\nAssisted by Mojodex"}
                      className="ml-1 mr-1"
                    >
                      <EmailIcon size={32} round />
                    </EmailShareButton>
                  </div>

                  <div className="flex justify-center items-center">
                    <IPhoneTextButton message={message} />
                  </div>
                </a>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default ShareButton;
