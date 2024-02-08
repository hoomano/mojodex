"use client";
import { useRouter } from "next/router";
import { Container } from "./Container";
import { useTranslation } from "next-i18next";


export function Hero() {
  const { t } = useTranslation("home");
  const router = useRouter();

  return (
    <div className="overflow-hidden py-0 md:py-8">
      <Container>
        <div className="flex items-center flex-col-reverse md:flex-row mx-auto lg:max-w-4xl sm:max-w-xl md:max-w-2xl text-center py-4 md:gap-x-8">
          <div className="flex-1">
            <h1 className="text-center md:text-left text-4xl font-medium tracking-tight text-gray-900">
              {t("hero.title")}
            </h1>
            <p className="text-center md:text-left mt-6 text-lg text-gray-600">
              {t("hero.description")}
            </p>
          </div>
          <div className="flex-1">
            <video playsInline autoPlay loop muted>
              <source
                src="/images/landing/landingPageAnimation_WebM.webm"
                type="video/webm"
              />
              <source
                src="/images/landing/landingPageAnimation.mp4"
                type="video/mp4"
              />
            </video>
          </div>
        </div>
      </Container>
    </div>
  );
}
