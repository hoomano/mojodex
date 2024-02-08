import Image from "next/image";

const AuthMobileView = () => {
  return (
    <div className="h-screen flex items-center sm:hidden">
      <div className="px-5 text-center">
        <div className="text-[32px] font-semibold">🦸‍♂️</div>
        <div className="my-2.5 text-[32px] font-semibold">
          A heroic experience awaits!
        </div>
        <div className="text-xl text-gray-lighter">
          Unlock your smartphone's superpowers with the Mojodex app
        </div>
        <div className="text-[32px] font-semibold">📱</div>
        <div className="mt-2.5 text-[32px] font-semibold">Download now</div>
        <div className="flex justify-center gap-2.5 pt-[60px]">
          <a
            href="https://play.google.com/store/apps/details?id=com.hoomano.mojodex_mobile"
            rel="noopener noreferrer"
          >
            <Image
              src="/images/google_play.svg"
              alt="google_play"
              width={120}
              height={34}
            />
          </a>
          <a
            href="https://apps.apple.com/fr/app/mojodex/id6446367743"
            rel="noopener noreferrer"
          >
            <Image
              src="/images/app_store.svg"
              alt="app_store"
              width={120}
              height={34}
            />
          </a>
        </div>
      </div>
    </div>
  );
};

export default AuthMobileView;
