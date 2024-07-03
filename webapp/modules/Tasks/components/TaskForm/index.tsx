import { useState } from "react";
import { ArrowLeftIcon } from "@heroicons/react/20/solid";
import { InputArrayProps } from "../../interface";
import { useRouter } from "next/router";
import useGetTaskConfigs from "modules/Tasks/hooks/useGetTaskConfigs";
import InputPlaceholder from "./InputPlaceholder";
import { decryptId, encryptId } from "helpers/method";
import Button from "components/Button";
import useGetTask from "modules/Tasks/hooks/useGetTask";
import usePostExecuteTask from "modules/Tasks/hooks/usePostExecuteTask";
import InputsForm from "./InputsForm";
import useAlert from "helpers/hooks/useAlert";
import { useTranslation } from "react-i18next";

const CreateTaskForm = () => {
  const router = useRouter();
  const { query } = router;
  const taskId = query.taskId ? decryptId(query.taskId as string) : null;
  const { t } = useTranslation('dynamic');

  const { data: task } = useGetTask(taskId);

  const [inputArray, setInputArray] = useState<InputArrayProps[]>([]);

  const { data: taskConfigDetails, isLoading } = useGetTaskConfigs(
    task?.user_task_pk
  );

  const sessionId = taskConfigDetails?.session_id;
  const taskExecutionPK = taskConfigDetails?.user_task_execution_pk;
  const tasksForm = taskConfigDetails?.json_input || [];
  const taskType = task?.task_type;
  const { showAlert } = useAlert();


  const { mutate: executeTaskMutation, isLoading: isPostExecuteTaskLoading } =
    usePostExecuteTask();

  const generateAnswerHandler = () => {
    //check inputArray contain every dict with key that were in tasksForm;
    for (let i = 0; i < tasksForm.length; i++) {
      if (!inputArray.find((input) => input.input_name === tasksForm[i].input_name || input.input_name.split("_").slice(0, -1).join("_") == tasksForm[i].input_name)) {
        showAlert({
          title: t("userTaskExecution.inputsTab.missingFieldLabel") + ":\n" + tasksForm[i].description_for_user,
          type: "error",
        });
        return;
      }
    }
      executeTaskMutation(
        {
          datetime: new Date().toISOString(),
          user_task_execution_pk: taskExecutionPK!,
          inputs: inputArray,
        },
        {
          onSuccess: () => {
            router.push(
              `/tasks/${encryptId(taskExecutionPK)}`
            );
          },
        }
      );
  };

  return (
    <div className="flex">
      <div className="flex-1">
        <div className="p-8 lg:p-16">
          <form>
            <>
              <div className="flex items-center">
                <ArrowLeftIcon
                  onClick={() => router.push("/tasks")}
                  className="w-[24px] h-[24px] text-gray-lighter cursor-pointer mr-2"
                />
              </div>

              <div className="flex flex-col text-center">
                <div>{task?.task_icon}</div>
                <div className="text-h3 font-semibold">
                  {task?.task_name}
                </div>
                <p className="text-h5 text-gray-lighter">
                  {task?.task_description}
                </p>
              </div>
            </>

            <div className="py-6">
              {!isLoading && taskConfigDetails ? <InputsForm
                jsonInputs={tasksForm}
                setInputArray={setInputArray}
                sessionId={sessionId!}
              />

                : (
                  <InputPlaceholder />
                )}
            </div>


            <div className="text-center">
              <Button
                onClick={generateAnswerHandler}
                disabled={!taskConfigDetails}
                variant="primary"
                className="min-w-[83px]"
              >
                Go
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateTaskForm;
