const Loading = () => {
  return (
    <div className="flex flex-col animate-pulse bg-gray-800  supports-[height:100cqh]:h-[100cqh] supports-[height:100svh]:h-[100svh]">
      <div className="h-60 flex-none m-2">
        <div className="flex flex-col h-full  rounded-md border-transparent focus:border-transparent  bg-gray-700 justify-center text-center items-center">
          <img src="images/logo/mojodex_logo.png" className="w-24 items-center" />
          <div className="text-white italic text-xs">powered by </div>
          <div className="text-white">Hoomano ©</div>
        </div>
      </div>
      <div className="flex flex-col h-full m-2 rounded-md py-2 border-transparent focus:border-transparent bg-gray-700" />

      <div className="flex m-2 sm:ml-12 md:ml-36 lg:ml-60 xl:ml-80 2xl:ml-96  sm:mr-12 md:mr-36 lg:mr-60 xl:mr-80 2xl:mr-96 ">
        <form className="flex flex-grow py-2 items-end">
          <div className="flex-1 rounded-md h-12 px-2 py-1 border-transparent focus:border-transparent focus:ring-0 text-white bg-gray-700 overflow-hidden justify-center text-center">
            Loading...
          </div>
        </form>
      </div>
    </div>
  );
};

export default Loading;
