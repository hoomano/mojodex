from datetime import datetime, timezone
from entities.message import Message

class UserTaskExecutionListElementDisplay:

    def __init__(self, icon, title, summary, start_date, produced_text_done, pk):
        self.icon = icon
        self.title = title
        self.summary = summary
        self.start_date = start_date
        self.produced_text_done = produced_text_done
        self.pk = pk

    # return a string representing the time since the task was started
    # e.g. "3h ago", "2d ago", "1w ago", "1m ago", "1y ago"
    @property
    def duration_ago(self):
        duration = datetime.now(timezone.utc) - datetime.fromisoformat(self.start_date)
        if duration.days > 365:
            return f"{duration.days // 365}y ago"
        if duration.days > 30:
            return f"{duration.days // 30}mo ago"
        if duration.days > 7:
            return f"{duration.days // 7}w ago"
        if duration.days > 1:
            return f"{duration.days}d ago"
        if duration.seconds > 3600:
            return f"{duration.seconds // 3600}h ago"
        if duration.seconds > 60:
            return f"{duration.seconds // 60}m ago"
        return f"{duration.seconds}s ago"

    def __str__(self) -> str:
        return f"{self.icon} {self.title}\n\n{self.summary}\n\n{self.duration_ago} {'✅' if self.produced_text_done else ''}\n"
    

class UserTaskExecutionResult:

    def __init__(self, title, result):
        self.title = title
        self.result = result

    @property
    def concatenated_result(self):
        return f"{self.title}\n{self.result}"
    
class NewUserTaskExecution:

    def __init__(self, pk, json_input, session_id):
        self.pk = pk
        self.json_input = json_input
        self.session_id = session_id
        self.result = None
    

    def new_result(self, title, result):
        self.result = UserTaskExecutionResult(title, result)

    @property
    def concatenated_result(self):
        return self.result.concatenated_result
    