import Modal from "components/Modal";
import { XMarkIcon } from "@heroicons/react/24/outline";
import Button from "components/Button";

interface TaskDoneModalType {
  isOpen: boolean;
  closed: () => void;
}

const TaskDoneModal = ({ isOpen, closed }: TaskDoneModalType) => {
  return (
    <div>
      <Modal
        isOpen={isOpen}
        footerPresent={false}
        headerPresent={false}
        widthClass="max-w-[880px]"
      >
        <div className="mx-auto p-14 text-center">
          <div className="flex items-center">
            <h3 className="text-h3 text-center flex-1 pb-2">
              Thank you! I'm on it!
            </h3>
            <XMarkIcon
              className="h-6 w-6 text-gray-lighter cursor-pointer"
              aria-hidden="true"
              onClick={closed}
            />
          </div>
          <div className="text-center text-gray-lighter">
            I'll put my AI smarts to work and suggest follow-up actions tailored
            to your needs. This process can take a little time, but don't worry.
            You can check back later in the 'Tasks' section to see my
            suggestions. Thanks for using Mojodex!
          </div>

          <Button className="mt-7" variant="primary" size="middle" onClick={closed}>
            Got it
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default TaskDoneModal;
