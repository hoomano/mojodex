import Onboarding from "modules/Onboarding";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

const OnboardingPage = () => {
  return <Onboarding />;
};

export default OnboardingPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
