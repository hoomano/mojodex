class AssistantMessageContext:
    logger_prefix = "AssistantMessageContext :: "

    def __init__(self, user):
        self.user = user
        

    @property
    def user_id(self):
        return self.user.user_id
    
    @property
    def username(self):
        return self.user.name