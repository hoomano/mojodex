
class User:
    def __init__(self, email, name, token):
        self.email = email
        self.name = name
        self.token = token
    
    def __str__(self):
        return f'{self.name} ({self.email})'
