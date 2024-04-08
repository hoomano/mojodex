import React, { useEffect, useState } from "react";
import Welcome from "./components/Welcome";
import BusinessDetails, {
  BusinessDetailsForm,
} from "./components/BusinessDetails";
import useRegisterCompany from "./hooks/useRegisterCompany";
import useUpdateCompanyDetails from "./hooks/useUpdateCompanyDetails";
import { useSession } from "next-auth/react";
import { useRouter } from "next/router";
// import Layout from "components/Layout";
import Goals from "./components/Goals";
import ProductCategories from "./components/ProductCategories";
import useUpdateBusinessGoal from "./hooks/useUpdateBusinessGoal";
import useUpdateCategory from "./hooks/useUpdateCategory";
import useAlert from "helpers/hooks/useAlert";
import useOnboardingPresented from "./hooks/useOnboardingPresented";
import { ProductCategory } from "./interface";
import { useTranslation } from "react-i18next";

declare let window: {
  chrome: any;
  postMessage: any;
  location: any;
};

declare let chrome: {
  runtime: any;
};

export enum OnboardingSteps {
  WELCOME = "Welcome",
  BUSINESS_LEARNING = "BUSINESS_LEARNING",
  BUSINESS_DETAILS = "BUSINESS_DETAILS",
  //BUSINESS_GOALS = "BUSINESS_GOALS",
  PRODUCT_CATEGORIES = "PRODUCT_CATEGORIES",
}

interface OnboardingStep {
  title: string;
  description: string;
  icon: string;
  children: React.ReactNode;
}

const Onboarding = () => {
  const { showAlert } = useAlert();
  const registerCompany = useRegisterCompany();
  const updateCompanyDetails = useUpdateCompanyDetails();
  const updateBusinessGoal = useUpdateBusinessGoal();
  const updateCategory = useUpdateCategory();
  const router = useRouter();
  const { t } = useTranslation("dynamic");
  const { update: updateAuthSession, data: session }: any = useSession();
  const [activeStep, setActiveStep] = useState<OnboardingSteps>(
    OnboardingSteps.PRODUCT_CATEGORIES
  );
  const editorExtensionId = process.env.NEXT_PUBLIC_EDITOR_EXTENSION_ID;

  const companyDetails: any = registerCompany?.data;

  const onboardingPresented = useOnboardingPresented();

  useEffect(() => {
    if (
      session?.authorization?.onboarding_presented &&
      activeStep === OnboardingSteps.PRODUCT_CATEGORIES
    ) {
      router.push("/");
    }
  }, [session, activeStep]);

  const onProfileSubmit = (companyWebsite: string) => {
    setActiveStep(OnboardingSteps.BUSINESS_LEARNING);
    registerCompany.mutate(companyWebsite, {
      onSuccess: (data: any) => {
        updateAuthSession({
          ...session,
          authorization: {
            ...session.authorization,
            company_fk: data?.company_pk,
          },
        });
        setActiveStep(OnboardingSteps.BUSINESS_DETAILS);
      },
      onError: () => setActiveStep(OnboardingSteps.WELCOME),
    });
  };

  const onBusinessDetailsSubmit = (data: BusinessDetailsForm) => {
    updateCompanyDetails.mutate(data, {
      onSuccess: () => onboardingPresentedCheck(),
      onError: () => setActiveStep(OnboardingSteps.BUSINESS_DETAILS),
    });
  };


  const onboardingPresentedCheck = () => {
    const editorExtensionId = process.env.NEXT_PUBLIC_EDITOR_EXTENSION_ID;

    onboardingPresented.mutate(undefined, {
      onSuccess: () => {
        if (editorExtensionId && window?.chrome?.runtime?.sendMessage) {
          chrome.runtime.sendMessage(editorExtensionId, {
            message: {
              isLogin: true,
            },
          });
        }
        updateAuthSession({
          ...session,
          authorization: {
            ...session.authorization,
            onboarding_presented: true,
          },
        });
        setTimeout(() => {
          window.location.href =
            router.query.extension === "true" ? "/extension" : "/tasks";
        }, 500);
      },
      onError: (error: any) => {
        console.log(error, "error");
      },
    });
  };

  const setSelectedCategory = (item: ProductCategory) => {
    updateCategory.mutate(
      item.product_category_pk,
      {
        onSuccess: () => {
          setActiveStep(OnboardingSteps.WELCOME);
        },
        onError: (error: any) => {
          showAlert({
            title: error?.error || "Something went wrong!",
            type: "warning",
          });
        },
      }
    );
  }

  const onCategoryClick = (item: ProductCategory) => {
    setSelectedCategory(item);
  };

  const onBusinessDetailsGoalSubmit = (goal: string) => {
    if (goal === "Discover Mojodex") {
      onboardingPresentedCheck();
    } else {
      updateBusinessGoal.mutate(
        { goal },
        {
          onSuccess: () => {
            onboardingPresentedCheck();
          },
          onError: (error: any) => {
            showAlert({
              title: error?.error || "Something went wrong!",
              type: "warning",
            });
          },
        }
      );
    }
  };

  const steps: Record<OnboardingSteps, OnboardingStep> = {
    [OnboardingSteps.WELCOME]: {
      title: t("onboarding.webUrlInputPage.title"),
      description: t("onboarding.webUrlInputPage.body"),
      icon: t("onboarding.webUrlInputPage.emoji"),
      children: (
        <Welcome
          onProfileSubmit={onProfileSubmit}
          onboardingPresentedCheck={onboardingPresentedCheck}
        />
      ),
    },
    [OnboardingSteps.BUSINESS_LEARNING]: {
      title: "Give us a moment..",
      description: "While we’re learning a little bit more about your business",
      icon: "🔎",
      children: (
        <div className="w-[200px] mx-auto">
          <div className="bg-gray-200 rounded-full h-2 dark:bg-gray-700">
            <div className="bg-blue-600 w-[40%] h-2 rounded-full transition-all" />
          </div>
        </div>
      ),
    },
    [OnboardingSteps.BUSINESS_DETAILS]: {
      title: companyDetails?.company_name,
      description: companyDetails?.company_description,
      icon: companyDetails?.company_emoji,
      children: (
        <BusinessDetails
          onBusinessDetailsSubmit={onBusinessDetailsSubmit}
          isLoading={updateCompanyDetails?.isLoading}
          onboardingPresentedCheck={onboardingPresentedCheck}
        />
      ),
    },
    /*[OnboardingSteps.BUSINESS_GOALS]: {
      title: "What’s your main business goal?",
      description:
        "Tell us a bit about your yourself. This will help us assist you the best we can.",
      icon: "🎯",
      children: (
        <Goals
          onSubmit={onBusinessDetailsGoalSubmit}
          isLoading={updateBusinessGoal.isLoading}
          onboardingPresentedCheck={onboardingPresentedCheck}
        />
      ),
    },*/
    [OnboardingSteps.PRODUCT_CATEGORIES]: {
      title: t("onboarding.categorySelection.title"),
      description:
        `${t("onboarding.categorySelection.content")} ${t("onboarding.categorySelection.question")}`,
      icon: t("onboarding.categorySelection.emoji"),
      children: (
        <ProductCategories
          onCategoryClick={onCategoryClick}
        />
      ),
    },
  };

  const { title, description, icon, children } = steps[activeStep];

  const shouldExpandContent =
    activeStep === OnboardingSteps.WELCOME ||
    activeStep === OnboardingSteps.BUSINESS_DETAILS;

  const content = (
    <div
      className={`${shouldExpandContent ? "max-w-[580px]" : "max-w-[820px]"
        } mx-auto mt-[100px] flex justify-center px-5 sm:px-0`}
    >
      <div>
        <div className="text-center">
          <p className="text-[30px]">{icon}</p>
          <h2 className="text-h2 font-semibold">{title}</h2>
          <p className="text-h5 text-gray-lighter">{description}</p>
        </div>
        <div className="py-12">{children}</div>
      </div>
    </div>
  );


  return content;
};

export default Onboarding;
