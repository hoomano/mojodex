class TagManager:

    def __init__(self, tag_name):
        self.start_tag = f"<{tag_name}>"
        self.end_tag = f"</{tag_name}>"

    def extract_text(self, text):
        try:
            return text.split(self.start_tag)[1].split(self.end_tag)[0].strip() if self.start_tag in text else ""
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: tag: {self.start_tag} :: {e}")

    def add_tags_to_text(self, text):
        return f"{self.start_tag}{text}{self.end_tag}"