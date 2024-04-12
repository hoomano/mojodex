import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import Button from "components/Button";
import Modal from "components/Modal";
import useAcceptTermAndCondition from "helpers/hooks/useAcceptTermAndCondition";
import { useRouter } from "next/router";
import useUpdatePurchaseInSession from "helpers/hooks/useUpdatePurchaseInSession";
import { useTranslation } from "react-i18next";

const AcceptTermsAndConditionModal = () => {
  useUpdatePurchaseInSession();
  const [accepted, setAccepted] = useState(false);
  const [isTermsModalOpen, setIsTermsModalOpen] = useState(false);
  const router = useRouter();
  const { t } = useTranslation("dynamic");

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
          <div className="text-h3">{t("onboarding.termsAndConditions.title")}{" "}{t("onboarding.termsAndConditions.emoji")}</div>
          <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
            {t("onboarding.termsAndConditions.defaultModalContent")}
          </div>
          <div className="text-gray-lighter mt-5">
            <input
              checked={accepted}
              type="checkbox"
              onChange={(e) => setAccepted(e.target.checked)}
              className="cursor-pointer outline-0 mr-2"
            />
            {t("onboarding.termsAndConditions.defaultAgreement")}
          </div>
          <div className="text-gray-lighter mt-2">
            {t("onboarding.termsAndConditions.defaultAgreementThankYou")}
          </div>
        </>
      );
    } else {
      return (
        <>
          <div className="text-h3">{t("onboarding.termsAndConditions.title")}{" "}{t("onboarding.termsAndConditions.emoji")}</div>
          <div className="text-subtitle5 text-gray-lighter mt-2 mb-6">
            {t("onboarding.termsAndConditions.defaultModalContent")}
          </div>
          <div className="flex items-center justify-center text-gray-lighter mt-5">
            <input
              checked={accepted}
              type="checkbox"
              onChange={(e) => setAccepted(e.target.checked)}
              className="cursor-pointer outline-0 mr-2"
            />
            {t("onboarding.termsAndConditions.IAgree")}{" "}
            <Link href={termsOfUseLink as string} target="_blank" className="ml-1">
              {t("onboarding.termsAndConditions.termsAndConditions")}
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
            {t("onboarding.termsAndConditions.acceptButtonText")}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default AcceptTermsAndConditionModal;