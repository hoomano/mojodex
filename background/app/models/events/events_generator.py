import os
from abc import ABC, abstractmethod
from datetime import datetime

import requests


class EventsGenerator(ABC):
    send_events_url = f"{os.environ['MOJODEX_BACKEND_URI']}/event"

    @abstractmethod
    def generate_events(self, *args, **kwargs):
        pass

    def send_event(self, user_id, message, event_type, data=None):
        if data is None:
            data = {}
        try:
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'user_id': user_id,
                     'message': message, 'event_type': event_type, 'data':data
                     }
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(EventsGenerator.send_events_url, json=pload, headers=headers)
            if internal_request.status_code != 200:
                # An error occurred but have probably already been logged in the backend
                return None
            return internal_request.json()["event_pk"]
        except Exception as e:
            raise Exception(f"_send_event: " + str(e))