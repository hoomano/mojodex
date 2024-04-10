import { useState, useEffect, useContext } from "react";
import { ArrowLeftIcon } from "@heroicons/react/20/solid";
import { InputArrayProps, TaskPreference, UserTask } from "../../interface";
import globalContext from "helpers/GlobalContext";
import { useRouter } from "next/router";
import useGetTaskConfigs from "modules/Tasks/hooks/useGetTaskConfigs";
import InputPlaceholder from "./InputPlaceholder";
import Textarea from "./TextArea";
import PrefSwitchGroup from "./PrefSwitchGroup";
import { decryptId, encryptId } from "helpers/method";
import Button from "components/Button";
import useGetTask from "modules/Tasks/hooks/useGetTask";
import { useTranslation } from "react-i18next";
import usePostExecuteTask from "modules/Tasks/hooks/usePostExecuteTask";

const CreateTaskForm = () => {
  const router = useRouter();
  const { query } = router;
  const taskId = query.taskId ? decryptId(query.taskId as string) : null;

  const { data: task } = useGetTask(taskId);
  const { setGlobalState }: any = useContext(globalContext);

  const [inputArray, setInputArray] = useState<InputArrayProps[]>([]);

  const { data: taskConfigDetails, isLoading } = useGetTaskConfigs(
    task?.user_task_pk
  );

  const sessionId = taskConfigDetails?.session_id;
  const taskExecutionPK = taskConfigDetails?.user_task_execution_pk;
  const tasksForm = taskConfigDetails?.json_input || [];
  const taskType = task?.task_type;

  const { t } = useTranslation("dynamic");

  const { mutate: executeTaskMutation, isLoading: isPostExecuteTaskLoading } =
    usePostExecuteTask();

  const generateAnswerHandler = () => {
    if (inputArray.length == tasksForm.length && taskExecutionPK && sessionId && taskType) {
      executeTaskMutation(
        {
          datetime: new Date().toISOString(),
          user_task_execution_pk: taskExecutionPK,
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
      
    } else {
      alert("Field missing");
    }
  };

  let counter = 1;
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
              <div className="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
                {!isLoading && taskConfigDetails ? (
                  tasksForm.map((input) => (
                    <Textarea
                      key={input.input_name}
                      jsonInput={input}
                      setInputArray={setInputArray}
                    />
                  ))
                ) : (
                  <InputPlaceholder />
                )}
              </div>
            </div>

            {task?.steps?.length ?? 0 > 0 ?
              (<div className="py-6">
                <p>
                  <div className="text-h3">{t("startUserTaskStepExecution.stepsIntroduction")}</div>
                </p>

                {!isLoading && taskConfigDetails ?
                  task?.steps.map((step) => (
                    <p className="text-h5 text-gray-lighter pt-1" key={"workflow_step_number_".concat(String(counter))}>
                      {counter++}. {step.step_definition_for_user}
                    </p>
                  )) : (
                    <p className="text-h5 text-gray-lighter">Loading...</p>
                  )}
              </div>) : null

            }


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
