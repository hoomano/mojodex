import { useMutation } from "@tanstack/react-query";
import { addDocument } from "services/resources";

const useAddDocument = () => useMutation(addDocument);

export default useAddDocument;
