import React, { useContext } from "react";
import moment from "moment";
import { useRouter } from "next/router";
import DraftCard from "components/DraftCard";
import { BeatLoader } from "react-spinners";
import useGetAllDrafts from "./hooks/useGetAllDrafts";
import { debounce, encryptId } from "helpers/method";
import globalContext, { GlobalContextType } from "helpers/GlobalContext";

const Drafts = () => {
  const {
    setGlobalState,
  } = useContext(globalContext) as GlobalContextType;

  const router = useRouter();

  const {
    fetchNextPage,
    data: draftResponse,
    isLoading,
    isFetching,
  } = useGetAllDrafts();

  const drafts =
    draftResponse?.pages?.flatMap((data) => data.produced_texts) || [];

  const handleRefetchOnScrollEnd = async (e: any) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (!isFetching && scrollHeight - scrollTop <= clientHeight * 1.2) {
      await fetchNextPage({ pageParam: drafts.length });
    }
  };

  const onCardClickHandler = (produced_text_pk: number) => {
    setGlobalState({ newlyCreatedTaskInfo: null } as any)
    router.push(`/drafts/${encryptId(produced_text_pk)}`)
  }

  return (
    <div
      className="w-full overflow-auto h-[calc(100vh-72px)] lg:h-screen"
      onScroll={debounce(handleRefetchOnScrollEnd)}
    >
      {isLoading ? (
        <div className="flex justify-center items-center h-screen w-full">
          <BeatLoader color="#3763E7" />
        </div>
      ) : (
        <ul role="list" className="grid-cols-1 mx-3 lg:mx-40  py-3 lg:py-10">
          {drafts?.length ? (
            drafts.map(
              ({ title, creation_date, production, produced_text_pk }) => (
                <DraftCard
                  key={produced_text_pk}
                  icon="📝"
                  title={title}
                  creationDate={moment(creation_date).fromNow()}
                  definition={production.slice(0, 200) + "..."}
                  onCardClick={() => onCardClickHandler(produced_text_pk)}
                />
              )
            )
          ) : (
            <div className="text-center text-2xl text-gray-400 py-10">
              Nothing to display here yet !
            </div>
          )}
        </ul>
      )}
    </div>
  );
};

export default Drafts;
