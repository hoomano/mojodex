import requests
from entities.user_task_execution import UserTaskExecutionListElementDisplay
from constants import SERVER_URL
from datetime import datetime

class User:
    def __init__(self, email, name, token):
        self.email = email
        self.name = name
        self.token = token
    
    def __str__(self):
        return f'{self.name} ({self.email})'
    

    def load_task_execution_list(self) -> list[UserTaskExecutionListElementDisplay]:
        try:
            print(f"Loading task execution list for {self.email}...")
            url = f"{SERVER_URL}/user_task_execution"

            headers = {
            'Authorization': self.token
            }

            # TODO: check platform: webapp
            response = requests.request("GET", url, headers=headers, params={"datetime": datetime.now().isoformat(), "platform": "mobile", "version": "0.0.0", "offset": 0, "n_user_task_executions": 4})

            if response.status_code == 200:
                data = response.json()
                
                return [UserTaskExecutionListElementDisplay(
                    task['icon'], task['title'], task['summary'], task['start_date'], task['produced_text_pk'] is not None
                ) for task in data['user_task_executions']]
            else:
                print(response.text)
                raise Exception("Incorrect credentials")
        except Exception as e:
            raise Exception(f"Failed to load task execution list: {e}")
    
    def task_execution_list_as_str(self) -> str:
        return "\n".join([str(task) for task in self.load_task_execution_list()])

