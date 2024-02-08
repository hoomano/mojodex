import { QueryClient } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 10,
      retry: 0,
      suspense: false,
      refetchOnWindowFocus: false,
    },
  },
});

export const invalidateQuery = (queryKey: any) =>
  queryClient.invalidateQueries({ queryKey });

export default queryClient;
