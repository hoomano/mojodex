from models.assistant.chat_assistant import ChatAssistant


class TagManager:

    def __init__(self, tag_name, placeholder_text):
        self.start_tag = f"<{tag_name}>"
        self.end_tag = f"</{tag_name}>"
        self._placeholder_text = placeholder_text

    @property
    def placeholder(self):
        return f"{self.start_tag}{self._placeholder_text}{self.end_tag}"

    def manage_text(self, text):
        try:
            mojo_text = ChatAssistant.remove_tags_from_text(text, self.start_tag, self.end_tag)
            return {"text": mojo_text,
                    "text_with_tags": text}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: tag: {self.start_tag} :: {e}")