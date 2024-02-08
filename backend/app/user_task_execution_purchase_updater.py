import os
from datetime import datetime

import socketio
from app import log_error
from mojodex_backend_logger import MojodexBackendLogger
import requests


class UserTaskExecutionPurchaseUpdater:
    logger_prefix = "UserTaskExecutionPurchaseUpdater:: "

    def __init__(self):
        try:
            self.logger = MojodexBackendLogger(UserTaskExecutionPurchaseUpdater.logger_prefix)
            self.sio = socketio.Client()
            self.__is_connected = False
            self.__connecting = False
            self.sio.on('error', self.error_handler)
            self.sio.on('connect', self.connect_callback)
            self.sio.on('draft_message', self.produced_text_callback)
            self.sio.on('mojo_message', self.mojo_message_callback)
            self.secret = os.environ["PURCHASE_UPDATER_SOCKETIO_SECRET"]
        except Exception as e:
            log_error(f"🔴 {self.logger_prefix} Error initializing purchase updater : {e}", notify_admin=True)

    # get is_connected
    @property
    def is_connected(self):
        return self.__is_connected

    # get connecting
    @property
    def connecting(self):
        return self.__connecting

    def connect(self):
        try:
            if self.__is_connected or self.__connecting:
                return
            self.logger.info(f"🟢 {self.logger_prefix} - connect")
            self.__connecting = True
            self.sio.connect('http://localhost:5000',
                             transports=['polling'], auth={'secret': self.secret})
        except Exception as e:
            self.__connecting = False
            log_error(f"🔴 {self.logger_prefix} Error connecting to socketio : {e}", notify_admin=True)

    def error_handler(self, msg):
        log_error(f"🔴 {self.logger_prefix} Error: {msg}", notify_admin=True)

    def connect_callback(self):
        self.logger.info(f"🟢 {self.logger_prefix} Connected")
        self.__is_connected = True
        self.__connecting = False

    def disconnect_callback(self):
        log_error(f"🟠 {self.logger_prefix} Disconnected", notify_admin=True)
        self.__is_connected = False
        self.__connecting = False

    def join_room(self, room):
        try:
            self.sio.emit('manage_session_events', {'room': room, 'secret': self.secret})
            self.logger.info(f"🟢 {self.logger_prefix} Joining room {room}")
        except Exception as e:
            log_error(f"🔴 {self.logger_prefix} Error joining room {room} : {e} "
                      f"- __is_connected: {self.__is_connected} - __connecting: {self.__connecting}", notify_admin=True)



    def produced_text_callback(self, msg):
        try:
            user_task_execution_pk = msg["user_task_execution_pk"]
            # make a call to POST /user_task_execution
            url = f"http://localhost:5000/user_task_execution"
            headers = {'Content-type': 'application/json', 'Authorization': self.secret}
            data = { "datetime": datetime.now().isoformat(),
                "user_task_execution_pk": user_task_execution_pk}
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                log_error(f"🔴 {self.logger_prefix} Error while associating purchase to user_task_execution : {response.text}",
                          notify_admin=True)
            return {'backend_event_manager': True}, # Do not remove the "," => important for socketio callback receiver

        except Exception as e:
            log_error(f"🔴 {self.logger_prefix} Error while associating purchase to user_task_execution : {e}",
                      notify_admin=True)
            return {'backend_event_manager': True}, # Do not remove the "," => important for socketio callback receiver

    def mojo_message_callback(self, msg):
        return {'backend_event_manager': True}, # Do not remove the "," => important for socketio callback receiver
