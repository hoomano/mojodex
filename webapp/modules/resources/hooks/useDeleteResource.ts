import { useMutation } from "@tanstack/react-query";
import { deleteResource } from "services/resources";

const useDeleteResource = () => useMutation(deleteResource)

export default useDeleteResource;