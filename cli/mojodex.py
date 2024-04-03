import os
import json
import requests
from getpass import getpass
import socketio

# Constants
BASE_DIR = os.path.expanduser('~/.mojodex')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials')
SERVER_URL = 'http://localhost:5001'

CURRENT_STATE = ""

CURRENT_STEP = None

# Initialize SocketIO client
sio = socketio.Client()


@sio.on('connect')
def on_connect():
    print('✅ Connected.')


@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from the server.')


@sio.on('workflow_step_execution_started')
def on_step_started(data):
    try:
        print(f"\n📩 Step {data['step_name']} started")
    except Exception as e:
        print(e)


@sio.on('workflow_step_execution_ended')
def on_step_ended(data):
    global CURRENT_STEP
    try:
        print(f"\n📩 Step {data['step_name']} ended")
        CURRENT_STEP = data
    except Exception as e:
        print(e)

def connect_to_session(session_id):
    sio.emit("start_session", {"session_id": session_id, "version": "0.0.0"})

def close_socket():
    print("\n🚦 Closing socket")
    sio.disconnect()


def validate_step(step_result):
    try:
        print("Results:")
        for result in step_result['result']:
            for key, value in result.items():
                print(f"{key}: {value}")
        validation_input = input("Validate step? (Y/n)")
        # if user press enter, it will be considered as 'Y'
        if not validation_input:
            print("no input specified, defaulting to 'Y'")
            validation_input = 'y'
        if validation_input.lower() == 'y':
            email, username, token = load_credentials()
            response = requests.post(
                f'{SERVER_URL}/user_workflow_step_execution', 
                params={"datetime": "now", "platform": "webapp", "user_workflow_step_execution_pk": step_result['user_workflow_step_execution_pk']},
                headers={'Authorization': f'{token}'},
                json={"user_workflow_step_execution_pk": step_result['user_workflow_step_execution_pk'],
                      "datetime": "now",
                    "validated": True,
                    "platform": "webapp"}
                )
            step_result = response.json()
            print(step_result)
        else:
            print("Step rejected.")
            print("Work in progress... (will provide reason as input to the server)")
    except Exception as e:
        print("Failed to validate step.")
        print(e)


def ensure_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)


def save_credentials(email, username, token):
    ensure_dir()
    with open(CREDENTIALS_FILE, 'w') as file:
        file.write(f"{email}:{username}:{token}")


def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            # Return email, username, token
            return file.read().strip().split(':')
    except FileNotFoundError:
        return None, None, None


def login():
    username = input('Username: ')
    password = getpass('Password: ')
    response = requests.post(f'{SERVER_URL}/user', json={'email': username,
                             'password': password, "login_method": "email_password", "datetime": "now"})
    if response.status_code == 200:
        data = response.json()
        save_credentials(username, data['name'], data['token'])
        return username, data['name'], data['token']
    else:
        print("Incorrect credentials. Please try again.")
        return None, None, None


def help_command():
    print("""
    Available commands:
    - workflow list | wl: List available workflows.
    - workflow run <workflow_id> | wr <workflow_id>: Run a specific workflow by ID.
    - workflow info <workflow_execution_pk> | wr <workflow_execution_pk>: Retrieve information about a workflow execution.
    - help: Show this help message.
    - exit | x | q | quit: Exit Mojodex.
    """)


def workflow_list():
    try:
        email, username, token = load_credentials()
        if not token:
            print("Please login first.")
            return
        # Placeholder for the actual request to list workflows
        response = requests.get(f'{SERVER_URL}/user_workflow', headers={'Authorization': f'{token}'},
                                params={"datetime": "now", "platform": "webapp", "version": "0.0.0"})
        if response.status_code != 200:
            print("Failed to list workflows.")
            print(response.text)
            return
        else:
            workflows = response.json()['user_workflows']
            for workflow in workflows:
                print(
                    f"{workflow['user_workflow_pk']}. {workflow['icon']} {workflow['name']} - {workflow['description']}")
    except Exception as e:
        print("Failed to list workflows.")
        print(e)


def workflow_run(workflow_id):
    try:
        email, username, token = load_credentials()

        if not token:
            print("Please login first.")
            return
        # Create the workflow execution
        response = requests.put(f'{SERVER_URL}/user_workflow_execution', json={
            "datetime": "now",
            "user_workflow_pk": workflow_id,
            "platform": "webapp"
        }, headers={'Authorization': f'{token}'})
        if response.status_code == 200:
            workflow = response.json()
            # print(f"Workflow started\n{workflow}")
            connect_to_session(workflow['session_id'])
            values = []
            for input_spec in workflow['inputs']:
                value = input(f"{input_spec['input_name']}: ")
                values.append(
                    {"input_name": input_spec['input_name'], "value": value})
            # Run the workflow execution with the provided inputs
            # print(f"values: {values}")
            run_response = requests.post(f'{SERVER_URL}/user_workflow_execution', json={
                "user_workflow_execution_pk": workflow['user_workflow_execution_pk'],
                "datetime": "now",
                "platform": "webapp",
                "json_inputs": values
            }, headers={'Authorization': f'{token}'})
            if run_response.status_code == 200:
                print("Workflow started.")
                print(run_response.text)
            else:
                print(run_response.text)
                print("Failed to run the workflow.")
        else:
            print(response.text)
            print("Failed to run the workflow.")
    except Exception as e:
        print("Failed to run the workflow.")
        print(e)

# retrieve workflow execution information


def workflow_info(workflow_execution_pk):
    try:
        email, username, token = load_credentials()

        if not token:
            print("Please login first.")
            return
        response = requests.get(
            f'{SERVER_URL}/user_workflow_execution', headers={'Authorization': f'{token}'}, params={"user_workflow_execution_pk": workflow_execution_pk, "datetime": "now", "platform": "webapp"})
        if response.status_code == 200:
            workflow_execution = response.json()
            print(f"Workflow execution: {workflow_execution}")
        else:
            print("Failed to retrieve workflow execution information.")
            print(response.text)
    except Exception as e:
        print("Failed to retrieve workflow execution information.")
        print(e)


def main():
    email, username, token = load_credentials()
    if not token:
        print("Welcome to Mojodex! Please login.")
        email, username, token = login()
    print(f"How can I help, {username}?")
    sio.connect(SERVER_URL, transports=[
                'websocket'], auth={'token': token})
    while True:
        print(CURRENT_STATE)
        command = input("$> ").strip().split()
        if not command:
            continue
        if command[0] in ['exit', 'x', 'quit', 'q']:
            break
        elif command[0] == 'help':
            help_command()
        elif command[0] == 'v':
            validate_step(CURRENT_STEP)
        elif command[0] == 'wl':
            workflow_list()
        elif command[0] == 'wi' and len(command) == 2:
            workflow_info(command[1])
        elif command[0] == 'wr' and len(command) == 2:
            workflow_run(command[1])
        elif command[0] == 'workflow' or command[0] == 'wf':
            if len(command) < 2:
                print("Invalid command. Try 'help' for a list of commands.")
                continue
            if command[1] == 'list':
                workflow_list()
            elif command[1] == 'run' and len(command) == 3:
                workflow_run(command[2])
            else:
                print("Invalid workflow command. Try 'help' for a list of commands.")
        else:
            print("Unknown command. Try 'help' for a list of commands.")


if __name__ == '__main__':
    main()
