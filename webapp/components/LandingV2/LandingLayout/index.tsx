import { Footer } from "./Footer";
import { Header } from "./Header";

const LandingLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
      <Header />
      <main className="flex-auto">{children}</main>
      <Footer />
    </>
  );
};

export default LandingLayout;
