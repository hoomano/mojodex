
import { UserTaskExecutionStepExecution } from "modules/Tasks/interface";
import Button from "components/Button";
import useOnStepExecutionValidate from "modules/Tasks/hooks/useOnStepExecutionValidate";
import useOnStepExecutionInvalidate from "modules/Tasks/hooks/useOnStepExecutionInvalidate";
import useOnStepExecutionRelaunch from "modules/Tasks/hooks/useOnStepExecutionRelaunch";
import useOnSaveResultEdition from "modules/Tasks/hooks/useOnSaveResultEdition";
import TextareaAutosize from 'react-textarea-autosize';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid'
import BeatLoader from "react-spinners/BeatLoader";
import { useTranslation } from "next-i18next";
import { useState } from "react";
import StepResult from "./StepResult";
import useAlert from "helpers/hooks/useAlert";


interface StepProps {
    stepExecution: UserTaskExecutionStepExecution;
    sessionId: string;
    onInvalidate: any;
    onValidate: any;
    onStepRelaunched: any;
    onRestart: any;
    isFirstStep: boolean;
}

const Step: React.FC<StepProps> = ({
    stepExecution,
    sessionId,
    onInvalidate,
    onValidate,
    onStepRelaunched,
    onRestart,
    isFirstStep
}) => {
    const { t } = useTranslation('dynamic');
    const onSaveStepResultEdition = useOnSaveResultEdition();
    const onValidateStepExecution = useOnStepExecutionValidate();
    const onInvalidateStepExecution = useOnStepExecutionInvalidate();
    const onStepExecutionRelaunch = useOnStepExecutionRelaunch();
    const { showAlert } = useAlert();
    
    const calculateTimeAgo = (creationDate: string) => {
        const providedDate: any = new Date(creationDate);
        const currentDate: any = new Date();
        const timeDifference = currentDate - providedDate;

        // Calculate minutes, hours, and days
        const minutes = Math.floor(timeDifference / (1000 * 60));
        const hours = Math.floor(timeDifference / (1000 * 60 * 60));
        const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));

        let time_ago;

        if (minutes < 1) {
            time_ago = t('userTaskExecutionList.date.now');
        } else if (hours < 1) {
            time_ago = `${t('userTaskExecutionList.date.afterTimeAgo')} ${minutes}${t('userTaskExecutionList.date.minutes')} ${t('userTaskExecutionList.date.afterTimeAgo')}`;
        } else if (days < 1) {
            time_ago = `${t('userTaskExecutionList.date.beforeTimeAgo')}${hours}${t('userTaskExecutionList.date.hours')} ${t('userTaskExecutionList.date.afterTimeAgo')}`;
        } else if (days <= 7) {
            const dayOfWeek = [t('userTaskExecutionList.date.sunday'),
            t('userTaskExecutionList.date.monday'),
            t('userTaskExecutionList.date.tuesday'),
            t('userTaskExecutionList.date.wednesday'),
            t('userTaskExecutionList.date.thursday'),
            t('userTaskExecutionList.date.friday'),
            t('userTaskExecutionList.date.saturday')][providedDate.getDay()];
            const timeString = `${dayOfWeek} ${providedDate.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            })}`;
            time_ago = timeString;
        } else {
            time_ago = providedDate.toISOString().slice(0, 10);
        }

        return time_ago;
    };

    const [editing, setEditing] = useState<boolean>(false);
    const [editedResult, setEditedResult] = useState<Array<Map<string, string>>>([]);
    
    const onSaveResultEdition = () => {
        onSaveStepResultEdition.mutate({
            user_workflow_step_execution_pk: stepExecution.user_workflow_step_execution_pk,
            result: editedResult.map(obj => Object.fromEntries(obj))
        }, {
            onSuccess: (data) => {
                console.log(data);
                stepExecution.result = data['new_result'];
                console.log(stepExecution.result);
                setEditing(false);
            },
            onError: (error) => {
                showAlert({
                    title: t('errorMessages.globalSnackBarMessage'),
                    type: "error",
                });
            }
        });
    };
    
    const onReviewStep = () => {
        onInvalidateStepExecution.mutate(stepExecution.user_workflow_step_execution_pk, {
            onSuccess: () => {
                onInvalidate();
            },
            onError: (error) => {
                showAlert({
                    title: t('errorMessages.globalSnackBarMessage'),
                    type: "error",
                });
            }
        }
        );
    };

    const onRelaunchStep = () => {
        onStepExecutionRelaunch.mutate(stepExecution.user_workflow_step_execution_pk, {
            onSuccess: () => {
                onStepRelaunched(stepExecution.user_workflow_step_execution_pk);
            },
            onError: (error) => {
                showAlert({
                    title: t('errorMessages.globalSnackBarMessage'),
                    type: "error",
                });
            }
        }
        );
    };

    const onContinueStep = () => {
        onValidateStepExecution.mutate(stepExecution.user_workflow_step_execution_pk, {
            onSuccess: () => {
                onValidate(stepExecution.user_workflow_step_execution_pk);
            },
            onError: (error) => {
                showAlert({
                    title: t('errorMessages.globalSnackBarMessage'),
                    type: "error",
                });
            }
        }
        );
    };

    return (
       
            <>
                <div className="flex flex-row w-full">
                    <div className="relative h-6 w-6 flex-none items-center justify-center bg-white">
                        {stepExecution.validated === true ? (
                            <CheckCircleIcon className="h-6 w-6 text-primary-main" aria-hidden="true" />
                        ) : stepExecution.error_status != null ? (
                            <ExclamationCircleIcon className="h-6 w-6 text-red-500" aria-hidden="true" />
                        ) : (
                            <div className="mt-1.5 ml-2 h-1.5 w-1.5 rounded-full bg-gray-100 ring-1 ring-gray-300" />
                        )}
                    </div>
                    <div className="flex-col pl-3 w-full">
                        <div className="flex justify-between gap-x-4">
                            <div className="py-0.5 text-sm leading-5 text-gray-500">
                                {stepExecution.step_name_for_user}: <span className="font-medium text-gray-900">{stepExecution.step_definition_for_user}</span>
                            </div>
                            <time dateTime={stepExecution.creation_date} className="flex-none py-0.5 text-xs leading-5 text-gray-500">
                                {calculateTimeAgo(stepExecution.creation_date)}
                            </time>
                        </div>
                        <div className="flex-auto rounded-md p-3 ring-1 ring-inset ring-gray-200 w-full">

                            {
                                Object.entries(stepExecution.parameter).map(([key, value]) => (
                                    <p className="flex-auto text-xs leading-5 text-gray-500 italic">
                                        <span className="font-medium text-gray-400">{t("userTaskExecution.processTab.stepExecutionParameters")}:</span><br />
                                        {key}: {value?.toString()}
                                    </p>
                                ))
                            }
                            {
                                stepExecution.result != null && stepExecution.result.length > 0 ?
                                    <div className="relative">
                                        <div className="absolute inset-0 flex items-center" aria-hidden="true">
                                            <div className="w-full border-t border-gray-300" />
                                        </div>
                                        <div className="relative flex justify-center">
                                            <span className="bg-white px-2 text-xs text-gray-400">{t("userTaskExecution.processTab.stepExecutionResults")}</span>
                                        </div>
                                    </div> : (stepExecution.error_status === null ? <BeatLoader color="#3763E7" /> :
                                        <div className="relative">
                                            <p className="text-primary-main text-sm leading-5"> {t("userTaskExecution.processTab.stepExecutionError")}</p>
                                            <p className="text-gray-dark text-sm leading-5">{t("userTaskExecution.processTab.stepExecutionErrorInstruction")}</p>
                                        </div>
                                    )
                            }
                        <StepResult
                            stepExecutionResult={stepExecution.result}
                            sessionId={sessionId}
                            editing={editing}
                            editedResult={editedResult}
                            setEditedResult={setEditedResult}
                        />
                            {editing ? <div className="text-end pt-2">
                                <Button
                                    variant="outline"
                                    size="middle"
                                    onClick={() => setEditing(false)}
                                    className="mr-2"
                                >
                                {t("userTaskExecution.processTab.cancelEditionButton")}
                                </Button>

                                <Button variant="primary" size="middle" onClick={() => onSaveResultEdition()}>
                                {t("userTaskExecution.processTab.saveEditionButton")}
                                </Button>
                            </div> : stepExecution.user_validation_required && stepExecution.validated === null && stepExecution.result != null ?
                                <div className="text-end pt-2">
                                    {isFirstStep ? <Button
                                        variant="outline"
                                        size="middle"
                                        tooltip={t("userTaskExecution.processTab.restartButtonTooltip")}
                                        onClick={() => {
                                            // change tab => back to "initial data"
                                            onRestart();
                                        }}
                                        className="mr-2"
                                    >
                                        {t("userTaskExecution.processTab.restartButton")}
                                    </Button>: null}
                                    <Button
                                        variant="outline"
                                        size="middle"
                                            onClick={() => {
                                                setEditedResult(stepExecution.result.map(obj => new Map(Object.entries(obj))));
                                                setEditing(true)
                                            }}
                                        className="mr-2"
                                        tooltip={t("userTaskExecution.processTab.editButtonTooltip")}
                                    >
                                        {t("userTaskExecution.processTab.editionButton")}
                                    </Button>
                                    {/*<Button
                                        variant="outline"
                                        size="middle"
                                        onClick={() => onReviewStep()}
                                        className="mr-2"
                                    >
                                        {t("userTaskExecution.processTab.invalidateButton")}
                                        </Button>*/}

                                    <Button variant="primary" size="middle"
                                        tooltip={t("userTaskExecution.processTab.validateButtonTooltip")}
                                        onClick={() => onContinueStep()}>
                                        {t("userTaskExecution.processTab.validateButton")}
                                    </Button>
                                </div> : null
                            }
                            {stepExecution.error_status != null ?
                                <div className="text-end pt-2">
                                    <Button
                                        variant="outline"
                                        size="middle"
                                        onClick={() => onRelaunchStep()}
                                        className="mr-2"
                                    >
                                        {t("userTaskExecution.processTab.relaunchButton")}
                                    </Button>
                                </div> : null
                            }
                        </div>
                    </div>
                </div>
            </>

    
    );
};

export default Step;