import Loader from "components/Loader";
import React from "react";
import { useTranslation } from "next-i18next";

const TaskLoader = () => {
  const { t } = useTranslation('dynamic');
  return (
    <div className="w-[100%] h-[100%] flex flex-col items-center justify-center">
      <img src="/images/writing.png" className="h-8 w-8 bg-white" />
      <div className="text-h2 font-semibold text-center py-[10px]">
        {t('userTaskExecution.loading.title')}
      </div>
      <div className="text-h5 text-gray-lighter">{t('userTaskExecution.loading.subtitle')}</div>
      <Loader />
    </div>
  );
};

export default TaskLoader;
