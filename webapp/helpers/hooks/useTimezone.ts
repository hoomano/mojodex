import { useMutation } from "@tanstack/react-query";
import { timezoneSet } from "services/general";

const useTimezone = () => useMutation(timezoneSet);

export default useTimezone;
