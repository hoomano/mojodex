from datetime import datetime, timezone

class UserTaskExecutionListElementDisplay:

    def __init__(self, icon, title, summary, start_date, produced_text_done):
        self.icon = icon
        self.title = title
        self.summary = summary
        self.start_date = start_date
        self.produced_text_done = produced_text_done

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
