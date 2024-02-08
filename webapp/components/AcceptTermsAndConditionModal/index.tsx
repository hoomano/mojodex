import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import Button from "components/Button";
import Modal from "components/Modal";
import useAcceptTermAndCondition from "helpers/hooks/useAcceptTermAndCondition";
import { useRouter } from "next/router";
import useUpdatePurchaseInSession from "helpers/hooks/useUpdatePurchaseInSession";

const AcceptTermsAndConditionModal = () => {
  useUpdatePurchaseInSession();
  const [accepted, setAccepted] = useState(false);
  const [isTermsModalOpen, setIsTermsModalOpen] = useState(false);
  const router = useRouter();

  // read if there is a link to the terms of use from an environment variable
  const termsOfUseLink = process.env.NEXT_PUBLIC_TERMS_OF_USE_LINK;

  const acceptTermsAndCondition = useAcceptTermAndCondition();
  const { update, status, data: session }: any = useSession();

  const acceptTermsAndConditionHandler = () => {
    acceptTermsAndCondition.mutate();
    if (session) {
      const updatedSession = {
        ...session,
        authorization: {
          ...session.authorization,
          terms_and_conditions_agreed: true,
        },
      };
      update(updatedSession);
    }
  };

  useEffect(() => {
    if (!termsOfUseLink && !session?.authorization?.terms_and_conditions_agreed) {
      if (router.pathname !== "/onboarding") {
        setIsTermsModalOpen(false);
      } else if (status === "authenticated") {
        setIsTermsModalOpen(true);
      }
    } else {
      setIsTermsModalOpen(false);
    }
  }, [router, session, status, termsOfUseLink]);

  const renderContent = () => {
    if (!termsOfUseLink) {
      return (
        <>
          <div className="text-h3">Welcome! 😉</div>
          <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
            Please take a moment to acknowledge our community guidelines:
          </div>
          <div className="text-gray-lighter mt-5">
            <input
              checked={accepted}
              type="checkbox"
              onChange={(e) => setAccepted(e.target.checked)}
              className="cursor-pointer outline-0 mr-2"
            />
            I agree to interact with the digital assistant in a respectful and courteous manner, recognizing the importance of kindness in our digital space.
          </div>
          <div className="text-gray-lighter mt-2">
            Your cooperation helps us maintain a positive environment for all users. Thank you for your understanding and support!
          </div>
        </>
      );
    } else {
      return (
        <>
          <div className="text-h3">Welcome! 😉</div>
          <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
            Just before we start, have a look at our terms & conditions.
          </div>
          <div className="flex items-center justify-center text-gray-lighter mt-5">
            <input
              checked={accepted}
              type="checkbox"
              onChange={(e) => setAccepted(e.target.checked)}
              className="cursor-pointer outline-0 mr-2"
            />
            I accept the{" "}
            <Link href={termsOfUseLink as string} target="_blank" className="ml-1">
              terms & conditions
            </Link>
          </div>
        </>
      );
    }
  };

  return (
    <Modal
      isOpen={isTermsModalOpen}
      footerPresent={false}
      headerPresent={false}
      widthClass="max-w-[880px] text-center"
    >
      <div className="p-[60px]">
        {renderContent()}
        <div className="mt-6">
          <Button disabled={!accepted} onClick={acceptTermsAndConditionHandler}>
            Let’s start
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default AcceptTermsAndConditionModal;