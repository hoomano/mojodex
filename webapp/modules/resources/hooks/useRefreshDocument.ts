import { useMutation } from "@tanstack/react-query";
import { refreshDocument } from "services/resources";

const useRefreshDocument = () => useMutation(refreshDocument);

export default useRefreshDocument;
