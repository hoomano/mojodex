import Link from "next/link";
import { Container } from "../common/Container";
// import { NavLinks } from "../common/NavLinks";
// import { TextField } from "../common/Fields";
// import Button from "components/Button";

export function Footer() {
  return (
    <footer className="border-t border-gray-200">
      <Container>
        <div className="flex flex-col items-center pb-12 pt-8 md:flex-row-reverse md:justify-between md:pt-6">
          <p className="mt-6 text-sm text-gray-500 md:mt-0">
            Made with ❤️ by Hoomano
            <br/>
            <a href="https://github.com/hoomano/mojodex" target="_blank">Star us on GitHub 🌟</a>
          </p>
        </div>
      </Container>
    </footer>
  );
}
