class UserTaskListElementDisplay:
    def __init__(self, icon: str, name: str, description: str, pk: int) -> None:
        self.icon = icon
        self.name = name
        self.description = description
        self.pk = pk

    def __str__(self) -> str:
        return f'{self.icon}  {self.name}\n{self.description}'