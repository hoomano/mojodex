import { useMutation } from "@tanstack/react-query";
import { saveResultEdition } from "services/tasks";


const useOnSaveResultEdition = () => useMutation(saveResultEdition);

export default useOnSaveResultEdition;