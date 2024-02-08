import { ReactElement } from "react";
import { Hero } from "components/LandingV2/common/Hero";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";
import LandingLayout from "components/LandingV2/LandingLayout";

const MainPage = () => {
  return (
    <>
      <Hero />
    </>
  );
};

MainPage.getLayout = (MainPage: ReactElement) => (
  <LandingLayout>{MainPage}</LandingLayout>
);

export default MainPage;

export async function getStaticProps({ locale }: any) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "home", "dynamic"])),
    },
  };
}
