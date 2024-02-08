import { useMutation } from "@tanstack/react-query";
import { languageCode } from "services/general";

const useLanguageCode = () => useMutation(languageCode);

export default useLanguageCode;
