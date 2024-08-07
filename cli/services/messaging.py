import socketio
from services.auth import ensure_authenticated
from constants import *


class Messaging:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Messaging, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            self.sio = socketio.Client()
            self._initialized = True
            self.notify : callable = print
            self.sio.on('connect', self.on_connect)
            self.sio.on('disconnect', self.on_disconnect)
            self.sio.on('mojo_message', self.on_mojo_message)
            self.sio.on('draft_message', self.on_draft_message)
            self.sio.on('mojo_token', self.on_mojo_token)
            self.sio.on('draft_token', self.on_draft_token)
            self.on_mojo_message_callback : callable = lambda x: None
            self.on_draft_message_callback : callable = lambda x: None
            self.on_mojo_token_callback : callable = lambda x: None
            self.on_draft_token_callback : callable = lambda x: None
            self.__class__._initialized = True
            # current_session_id represents a mojo chat session, which is different from the socketio session
            self.current_session_id = None


    def on_connect(self):
        # self.notify('✅ Connected.')
        pass

    def on_disconnect(self):
        # self.notify('Disconnected from the server.')
        pass

    def on_mojo_token(self, data):
        try:
            if data["session_id"] != self.current_session_id:
                return
            self.on_mojo_token_callback(data)
        except Exception as e:
            self.notify(e)
        

    def on_draft_token(self, data):
        try:
            if data["session_id"] != self.current_session_id:
                return
            self.on_draft_token_callback(data)
        except Exception as e:
            self.notify(e)
        
    def on_mojo_message(self, data):
        try:
            if data["session_id"] != self.current_session_id:
                return
            self.on_mojo_message_callback(data)
            return {"session_id": data["session_id"], "message_pk": data["message_pk"]}
        except Exception as e:
            self.notify(e)

    def on_draft_message(self, data):
        try:
            if data["session_id"] != self.current_session_id:
                return
            self.on_draft_message_callback(data)
            return {"session_id": data["session_id"], "produced_text_version_pk": data["produced_text_version_pk"]}
        except Exception as e:
            self.notify(e)

    def connect_to_session(self, session_id):
        # self.notify(f"📩 Connected to session {session_id}")
        self.current_session_id = session_id
        self.sio.emit("start_session", {"session_id": self.current_session_id, "version": APP_VERSION})

    def close_socket(self):
        # self.notify("🚦 Closing socket")
        self.sio.disconnect()

    @ensure_authenticated
    def start(self, token):
        self.sio.connect(SERVER_URL, transports=[
                'websocket'], auth={'token': token})
