import requests
from entities.user_task import UserTaskListElementDisplay
from entities.user_task_execution import UserTaskExecutionListElementDisplay, UserTaskExecutionResult
from constants import SERVER_URL
from datetime import datetime
from services.auth import ensure_authenticated

@ensure_authenticated
def load_task_execution_result(user_task_execution_pk, token) -> UserTaskExecutionResult :
    try:
        url = f"{SERVER_URL}/user_task_execution"

        headers = {
        'Authorization': token
        }

        response = requests.request("GET", url, headers=headers, params={"datetime": datetime.now().isoformat(), "platform": "mobile", "version": "0.0.0", "user_task_execution_pk": user_task_execution_pk})

        if response.status_code == 200:
            data = response.json()
            
            return UserTaskExecutionResult(data["produced_text_title"], data['produced_text_production'])
        else:
            raise Exception(response.content)

    except Exception as e:
        raise Exception(f"Failed to load task execution result: {e}")


@ensure_authenticated
def load_task_execution_list(token) -> list[UserTaskExecutionListElementDisplay]:
    try:
        url = f"{SERVER_URL}/user_task_execution"

        headers = {
        'Authorization': token
        }

        # TODO: check platform: webapp
        response = requests.request("GET", url, headers=headers, params={"datetime": datetime.now().isoformat(), "platform": "mobile", "version": "0.0.0", "offset": 0, "n_user_task_executions": 20})

        if response.status_code == 200:
            data = response.json()
            
            return [UserTaskExecutionListElementDisplay(
                task['icon'], task['title'], task['summary'], task['start_date'], task['produced_text_pk'] is not None, task['user_task_execution_pk']
            ) for task in data['user_task_executions']]
        else:
            raise Exception(response.content)
    except Exception as e:
        raise Exception(f"Failed to load task execution list: {e}")

@ensure_authenticated
def load_user_tasks_list(token) -> list[UserTaskListElementDisplay]:
    try:
        url = f"{SERVER_URL}/user_task"

        headers = {
        'Authorization': token
        }

        response = requests.request("GET", url, headers=headers, params={"datetime": datetime.now().isoformat(), "platform": "webapp", "version": "0.0.0", "offset": 0, "n_user_tasks": 20})

        if response.status_code == 200:
            data = response.json()
            
            return [UserTaskListElementDisplay(
                task['task_icon'], task['task_name'], task['task_description'], task['user_task_pk']
            ) for task in data['user_tasks']]
        else:
            raise Exception(response.content)


    except Exception as e:
        raise Exception(f"Failed to load user tasks list: {e}")