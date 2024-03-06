import threading

from app import db, server_socket
from mojodex_core.entities import *
from jinja2 import Template

from models.produced_text_manager import ProducedTextManager

from app import llm, llm_conf, llm_backup_conf


class DefaultChitChat:
    logger_prefix = "DefaultChitChat::"

    chit_chat_prompt = "/data/prompts/chit_chat/chit_chat_prompt.txt"
    chit_chat_generator = llm(
        llm_conf, label="CHIT_CHAT", llm_backup_conf=llm_backup_conf)

    _answer_user_acceptable_time = 6  # 3 s

    def __init__(self, session_id, user):
        self.session_id = session_id
        self.user = user
        self.n_times_answer_user_timer_called = 0
        self._answer_user_timer = threading.Timer(DefaultChitChat._answer_user_acceptable_time,
                                                  self._answer_user_acceptable_time_expired_callback)

    def _answer_user_acceptable_time_expired_callback(self):
        self.n_times_answer_user_timer_called += 1
        self._answer_user_timer = threading.Timer(DefaultChitChat._answer_user_acceptable_time,
                                                  self._answer_user_acceptable_time_expired_callback)
        self._answer_user_timer.start()

    def response_to_user_message(self, user_message, partial_text_callback):
        try:

            event_name, response_message = self._answer_user(
                user_message, partial_text_callback)

            return event_name, response_message
        except Exception as e:
            raise Exception(
                f"{DefaultChitChat.logger_prefix} :: response_to_user_message :: {e}")

    def _answer_user(self, user_message, partial_text_callback):
        try:
            self._answer_user_timer.start()
            with open(DefaultChitChat.chit_chat_prompt, "r") as f:
                template = Template(f.read())
                chit_chat_prompt = template.render(language=self.user.language_code,
                                                   user_summary=self.user.summary,
                                                   title_start_tag=ProducedTextManager.title_start_tag,
                                                   title_end_tag=ProducedTextManager.title_end_tag,
                                                   draft_start_tag=ProducedTextManager.draft_start_tag,
                                                   draft_end_tag=ProducedTextManager.draft_end_tag)

            displayed_workspace_draft = user_message.get(
                "displayed_workspace_draft", None)
            displayed_workspace_title = user_message.get(
                "displayed_workspace_title", None)
            last_user_text = user_message.get("text", "")
            current_title = f"{ProducedTextManager.title_start_tag}\n{displayed_workspace_title}\n{ProducedTextManager.title_end_tag}\n" if displayed_workspace_title is not None else ""
            current_draft = f"{ProducedTextManager.draft_start_tag}\n{displayed_workspace_draft}\n{ProducedTextManager.draft_end_tag}\n" if displayed_workspace_draft is not None else ""
            messages = [{"role": "system", "content": chit_chat_prompt}] + self._get_conversation_as_list(
                without_last_message=True) + \
                [{"role": "user", "content": current_title +
                    current_draft + last_user_text}]
            self._answer_user_timer.cancel()

            responses = DefaultChitChat.chit_chat_generator.chat(messages, self.user.user_id,
                                                                 temperature=0.8, max_tokens=500,
                                                                 stream=True,
                                                                 stream_callback=partial_text_callback)

            text = responses[0].strip()
            if ProducedTextManager.draft_start_tag in text:
                produced_text_manager = ProducedTextManager(
                    self.session_id, self.user.user_id)
                produced_text, produced_text_version = produced_text_manager.extract_and_save_produced_text(text,
                                                                                                            user_message)
                text_type = db.session.query(MdTextType.name).filter(
                    MdTextType.text_type_pk == produced_text_version.text_type_fk).first()[0]

                return 'mojo_message', {"text_with_tags": text,
                                        "text": ProducedTextManager.remove_tags(text),
                                        "produced_text": produced_text_version.production,
                                        "produced_text_title": produced_text_version.title,
                                        "produced_text_pk": produced_text.produced_text_pk,
                                        "produced_text_version_pk": produced_text_version.produced_text_version_pk,
                                        "text_type": text_type}

            return 'mojo_message', {"text": text}
        except Exception as e:
            raise Exception(f"_answer_user:  " + str(e))

    def _get_conversation_as_list(self, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).order_by(
                MdMessage.message_date).all()
            if without_last_message:
                messages = messages[:-1]
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append(
                            {"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append(
                                {"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append(
                                {"role": agent_key, "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("Error during _get_conversation: " + str(e))
