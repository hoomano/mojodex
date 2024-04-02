
class Workflow:
    def __init__(self, db_object):
        self.db_object = db_object

    @property
    def name(self):
        return self.db_object.name

    @property
    def description(self):
        return self.db_object.description