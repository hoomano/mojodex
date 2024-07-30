from datetime import timedelta
import json

class TranscriptionWithTimeStamps:
    def __init__(self, text: str, start_time: timedelta, end_time: timedelta):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
    
    def __str__(self) -> str:
        start_ms = int(self.start_time.total_seconds() * 1000)
        end_ms = int(self.end_time.total_seconds() * 1000)
        return f"[{start_ms}ms-{end_ms}ms] {self.text}"
    
    def to_json(self) -> dict:
        return {
            "text": self.text,
            "start_time": self.start_time.total_seconds(),
            "end_time": self.end_time.total_seconds()
        }
    
    def to_json_string(self) -> str:
        return json.dumps(self.to_json(), indent=4)
